#!/usr/bin/env python3
# coding=utf-8
# APSS — Battery Monitor Node
# Legge INA219 via I2C e pubblica su /battery (sensor_msgs/BatteryState)
# INA219: indirizzo 0x40, shunt R100 (0.1Ω)
# Batteria: Yuasa YTZ10S AGM 12V 8.6Ah
# Versione: 1.0 — Maggio 2026

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import BatteryState
from apss_ros2_pkg.msg import BatteryStats
import board
import busio
from adafruit_ina219 import INA219
import math

# Tabella tensione → percentuale per batteria AGM 12V (scarica)
# Valori empirici — da calibrare sul campo
VOLTAGE_TABLE = [
    (12.70, 1.00),
    (12.50, 0.90),
    (12.30, 0.75),
    (12.10, 0.60),
    (11.90, 0.40),
    (11.75, 0.20),
    (11.60, 0.10),
    (11.50, 0.00),
]

def voltage_to_percentage(v):
    """Interpola la percentuale dalla tensione usando la tabella AGM."""
    if v >= VOLTAGE_TABLE[0][0]:
        return 1.0
    if v <= VOLTAGE_TABLE[-1][0]:
        return 0.0
    for i in range(len(VOLTAGE_TABLE) - 1):
        v_high, p_high = VOLTAGE_TABLE[i]
        v_low, p_low = VOLTAGE_TABLE[i + 1]
        if v_low <= v <= v_high:
            ratio = (v - v_low) / (v_high - v_low)
            return p_low + ratio * (p_high - p_low)
    return 0.0


class BatteryNode(Node):
    def __init__(self):
        super().__init__('battery_node')
        self.publisher_ = self.create_publisher(BatteryState, '/battery', 10)
        self.stats_publisher_ = self.create_publisher(BatteryStats, '/battery/stats', 10)
        self.v_min = float('inf')
        self.v_max = float('-inf')
        self.i_min = float('inf')
        self.i_max = float('-inf')
        self.p_min = float('inf')
        self.p_max = float('-inf')
        self.sample_count = 0
        self.timer = self.create_timer(2.0, self.publish_battery)

        # Init INA219
        i2c = busio.I2C(board.SCL, board.SDA)
        self.ina = INA219(i2c, addr=0x40)
        self.get_logger().info('[BATTERY] Node avviato — INA219 su 0x40')

    def publish_battery(self):
        try:
            voltage = self.ina.bus_voltage        # V
            current_ma = self.ina.current         # mA
            current_a = current_ma / 1000.0       # A
            power_w = voltage * abs(current_a)    # W calcolato V×I

            percentage = voltage_to_percentage(voltage)

            self.sample_count += 1
            self.v_min = min(self.v_min, voltage)
            self.v_max = max(self.v_max, voltage)
            self.i_min = min(self.i_min, current_a)
            self.i_max = max(self.i_max, current_a)
            self.p_min = min(self.p_min, power_w)
            self.p_max = max(self.p_max, power_w)

            # Determina status da segno corrente
            if current_a > 0.05:
                status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
            elif current_a < -0.05:
                status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
            else:
                status = BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING

            msg = BatteryState()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'battery'
            msg.voltage = float(voltage)
            msg.current = float(current_a)        # negativo=discharge, positivo=charge
            msg.percentage = float(percentage)
            msg.design_capacity = 8.6             # Ah — Yuasa YTZ10S
            msg.capacity = float('nan')
            msg.charge = float('nan')
            msg.temperature = float('nan')
            msg.power_supply_status = status
            msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
            msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_UNKNOWN
            msg.present = True
            msg.location = 'main'
            msg.serial_number = 'YTZ10S'

            self.publisher_.publish(msg)

            stats = BatteryStats()
            stats.header.stamp = self.get_clock().now().to_msg()
            stats.header.frame_id = 'battery'
            stats.voltage_min = float(self.v_min)
            stats.voltage_max = float(self.v_max)
            stats.current_min = float(self.i_min)
            stats.current_max = float(self.i_max)
            stats.power_min = float(self.p_min)
            stats.power_max = float(self.p_max)
            stats.sample_count = self.sample_count
            self.stats_publisher_.publish(stats)

            self.get_logger().info(
                f'[BATTERY] V={voltage:.3f}V  I={current_a:.3f}A  '
                f'P={power_w:.2f}W  SoC={percentage*100:.0f}%  status={status}'
            )

        except Exception as e:
            self.get_logger().error(f'[BATTERY] Errore lettura INA219: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = BatteryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
