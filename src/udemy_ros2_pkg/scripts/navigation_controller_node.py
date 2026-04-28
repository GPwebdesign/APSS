#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Navigation Controller Node
Subscriber: /obstacle/camera (std_msgs/String — JSON)
Publisher:  /cmd_vel (geometry_msgs/Twist)
TCP:        fallback diretto a rosmaster_main.py porta 6000

Gestisce la logica di navigazione: MOVING → STOPPING → ROTATING → MOVING
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import json
import socket
import threading
import time


class NavigationControllerNode(Node):

    # Stati macchina
    STATE_MOVING   = 'MOVING'
    STATE_STOPPING = 'STOPPING'
    STATE_ROTATING = 'ROTATING'

    def __init__(self):
        super().__init__('navigation_controller_node')

        # Parametri
        self.declare_parameter('linear_speed',   0.3)
        self.declare_parameter('angular_speed',  0.8)
        self.declare_parameter('rotate_duration', 1.5)
        self.declare_parameter('stop_duration',   0.5)
        self.declare_parameter('robot_ip',   '192.168.1.158')
        self.declare_parameter('tcp_port',   6000)
        self.declare_parameter('use_tcp',    True)
        self.declare_parameter('use_ros',    True)

        self.linear_speed    = self.get_parameter('linear_speed').value
        self.angular_speed   = self.get_parameter('angular_speed').value
        self.rotate_duration = self.get_parameter('rotate_duration').value
        self.stop_duration   = self.get_parameter('stop_duration').value
        self.robot_ip        = self.get_parameter('robot_ip').value
        self.tcp_port        = self.get_parameter('tcp_port').value
        self.use_tcp         = self.get_parameter('use_tcp').value
        self.use_ros         = self.get_parameter('use_ros').value

        # Subscriber / Publisher ROS2
        self.sub_obstacle = self.create_subscription(
            String, '/obstacle/camera', self._obstacle_cb, 10)
        self.pub_cmd_vel = self.create_publisher(Twist, '/cmd_vel', 10)

        # Stato macchina
        self._state       = self.STATE_MOVING
        self._state_lock  = threading.Lock()
        self._last_obstacle = 'none'

        # TCP client
        self._tcp_sock = None
        self._tcp_lock = threading.Lock()
        if self.use_tcp:
            self._connect_tcp()

        # Timer controllo navigazione 10Hz
        self.create_timer(0.1, self._navigation_tick)

        self.get_logger().info('Navigation Controller Node avviato!')
        self.get_logger().info(f'TCP: {self.use_tcp} — ROS: {self.use_ros}')

    # ── TCP ──────────────────────────────────────────────────────────────
    def _connect_tcp(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3.0)
            sock.connect((self.robot_ip, self.tcp_port))
            sock.settimeout(None)
            with self._tcp_lock:
                self._tcp_sock = sock
            # Inizializzazione modalita Standard
            self._tcp_send(b'$020f040116#')
            self.get_logger().info(f'TCP connesso a {self.robot_ip}:{self.tcp_port}')
        except Exception as e:
            self.get_logger().warn(f'TCP non disponibile: {e}')

    def _tcp_send(self, data: bytes):
        with self._tcp_lock:
            if self._tcp_sock:
                try:
                    self._tcp_sock.sendall(data)
                except Exception:
                    self._tcp_sock = None

    def _build_motor_cmd(self, vx, vy, vz, speed=50):
        """Cinematica Mecanum custom — cmd 0x1A."""
        m1 = vx - vy + vz
        m2 = vx + vy - vz
        m3 = vx + vy + vz
        m4 = vx - vy - vz
        max_val = max(abs(m1), abs(m2), abs(m3), abs(m4), 1)
        m1 = int(m1 / max_val * speed) & 0xFF
        m2 = int(m2 / max_val * speed) & 0xFF
        m3 = int(m3 / max_val * speed) & 0xFF
        m4 = int(m4 / max_val * speed) & 0xFF
        data = [0x02, 0x1A, 0x0C, m1, m2, m3, m4, 0x00]
        checksum = sum(data) % 256
        hex_str = ''.join(f'{b:02x}' for b in data)
        return f'${hex_str}{checksum:02x}#'.encode()

    # ── ROS2 cmd_vel ─────────────────────────────────────────────────────
    def _publish_twist(self, linear_x=0.0, angular_z=0.0):
        if not self.use_ros:
            return
        msg = Twist()
        msg.linear.x  = linear_x
        msg.angular.z = angular_z
        self.pub_cmd_vel.publish(msg)

    # ── Comando combinato ROS2 + TCP ──────────────────────────────────────
    def _move(self, vx=0.0, vy=0.0, vz=0.0):
        self._publish_twist(linear_x=vx, angular_z=vz)
        if self.use_tcp:
            self._tcp_send(self._build_motor_cmd(vx, vy, vz))

    def _stop(self):
        self._publish_twist(0.0, 0.0)
        if self.use_tcp:
            self._tcp_send(self._build_motor_cmd(0, 0, 0))

    # ── Obstacle callback ─────────────────────────────────────────────────
    def _obstacle_cb(self, msg: String):
        try:
            data = json.loads(msg.data)
            self._last_obstacle = data.get('direction', 'none')
        except Exception:
            pass

    # ── State machine tick 10Hz ───────────────────────────────────────────
    def _navigation_tick(self):
        with self._state_lock:
            state = self._state

        if state == self.STATE_MOVING:
            if self._last_obstacle != 'none':
                self.get_logger().info(
                    f'Ostacolo rilevato: {self._last_obstacle} — STOP')
                self._stop()
                with self._state_lock:
                    self._state = self.STATE_STOPPING
                # Avvia sequenza stop→rotate in thread separato
                threading.Thread(
                    target=self._avoidance_sequence,
                    args=(self._last_obstacle,),
                    daemon=True).start()
            else:
                self._move(vx=self.linear_speed)

        elif state in (self.STATE_STOPPING, self.STATE_ROTATING):
            pass  # gestito dal thread avoidance_sequence

    def _avoidance_sequence(self, obstacle_direction: str):
        # STOP
        self._stop()
        time.sleep(self.stop_duration)

        # Scegli direzione rotazione
        if obstacle_direction == 'left':
            rotate_vz = -self.angular_speed   # ruota destra
        elif obstacle_direction == 'right':
            rotate_vz = self.angular_speed    # ruota sinistra
        else:  # center o full
            rotate_vz = self.angular_speed    # ruota sinistra di default

        # ROTATE
        with self._state_lock:
            self._state = self.STATE_ROTATING
        self.get_logger().info(
            f'Rotazione {"sinistra" if rotate_vz > 0 else "destra"} per {self.rotate_duration}s')
        self._move(vz=rotate_vz)
        time.sleep(self.rotate_duration)

        # RESUME MOVING
        self._stop()
        self._last_obstacle = 'none'
        with self._state_lock:
            self._state = self.STATE_MOVING
        self.get_logger().info('Ripresa navigazione')


def main(args=None):
    rclpy.init(args=args)
    node = NavigationControllerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
