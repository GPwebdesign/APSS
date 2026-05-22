#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Obstacle Detector Node (Camera)
Subscriber: /image_raw (sensor_msgs/Image)
Publisher:  /obstacle/camera (std_msgs/String — JSON)

Rileva ostacoli nella ROI inferiore del frame usando analisi contorni OpenCV.
Pubblica direzione ostacolo: none / left / center / right / full
"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from sensor_msgs.msg import Image as RosImage
from std_msgs.msg import String
import cv2 as cv
import numpy as np
import json


class ObstacleDetectorNode(Node):

    def __init__(self):
        super().__init__('obstacle_detector_node')

        # Parametri configurabili
        self.declare_parameter('roi_top', 0.90)
        self.declare_parameter('min_contour_area', 250)
        self.declare_parameter('threshold', 60)
        self.declare_parameter('debug_image', False)

        self.roi_top       = self.get_parameter('roi_top').value
        self.min_area      = self.get_parameter('min_contour_area').value
        self.threshold     = self.get_parameter('threshold').value
        self.debug_image   = self.get_parameter('debug_image').value

        # Subscriber / Publisher
        self.sub = self.create_subscription(
            Image, '/image_raw', self._image_cb, 10)
        self.pub = self.create_publisher(String, '/obstacle/camera', 10)
        self.pub_debug = self.create_publisher(
            RosImage, '/obstacle/debug_image', 10)

        self.get_logger().info('Obstacle Detector Node avviato!')

    def _image_cb(self, msg: Image):
        # Converti ROS Image in numpy array BGR
        frame = np.frombuffer(msg.data, dtype=np.uint8).reshape(
            msg.height, msg.width, -1)
        if msg.encoding == 'rgb8':
            frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

        h, w = frame.shape[:2]
        roi_y = int(h * self.roi_top)

        # Estrai ROI inferiore
        roi = frame[roi_y:h, 0:w]

        # Binarizzazione su frame grigio
        gray  = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
        blur  = cv.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv.threshold(blur, self.threshold, 255, cv.THRESH_BINARY_INV)

        # Trova contorni
        contours, _ = cv.findContours(
            binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

        # Filtra contorni significativi
        valid = [c for c in contours if cv.contourArea(c) > self.min_area]

        for c in valid:
            x, y, cw, ch = cv.boundingRect(c)
            cx = x + cw // 2
            self.get_logger().info(
                f'Contorno: x={x} y={y} w={cw} h={ch} cx={cx} third={w//3}')

        direction = 'none'
        if valid:
            third = w // 3
            left_count   = 0
            center_count = 0
            right_count  = 0
            for c in valid:
                x, y, cw, ch = cv.boundingRect(c)
                cx = x + cw // 2  # centro orizzontale contorno
                if cx < third:
                    left_count += 1
                elif cx > 2 * third:
                    right_count += 1
                else:
                    center_count += 1

            total = left_count + center_count + right_count
            if left_count > 0 and right_count > 0:
                direction = 'full'
            elif center_count > 0:
                direction = 'center'
            elif left_count > 0:
                direction = 'left'
            elif right_count > 0:
                direction = 'right'

        # Pubblica risultato
        payload = json.dumps({
            'direction': direction,
            'contours':  len(valid),
            'source':    'camera'
        })
        self.pub.publish(String(data=payload))

        if self.debug_image:
            self.get_logger().info(f'Obstacle: {direction} ({len(valid)} contours)')

        # ── Debug image con ROI e contorni ──────────────
        try:
            debug = frame.copy()
            h, w = debug.shape[:2]
            roi_y = int(h * self.roi_top)
            # Linea ROI
            cv.line(debug, (0, roi_y), (w, roi_y), (0, 255, 0), 1)
            # Terzi verticali
            third = w // 3
            cv.line(debug, (third, roi_y), (third, h), (255, 255, 0), 1)
            cv.line(debug, (2*third, roi_y), (2*third, h), (255, 255, 0), 1)
            # Contorni validi
            for c in valid:
                x, y, cw, ch = cv.boundingRect(c)
                cv.rectangle(debug, (x, roi_y+y), (x+cw, roi_y+y+ch), (0, 0, 255), 1)
            # Direzione
            color = (0, 0, 255) if direction != 'none' else (0, 255, 0)
            cv.putText(debug, f"dir:{direction} th:{self.threshold}",
                       (2, 12), cv.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
            # Pubblica debug image
            debug_msg = RosImage()
            debug_msg.header.stamp = msg.header.stamp
            debug_msg.header.frame_id = 'camera_link'
            debug_msg.height = debug.shape[0]
            debug_msg.width  = debug.shape[1]
            debug_msg.encoding = 'bgr8'
            debug_msg.step = debug.shape[1] * 3
            debug_msg.data = debug.tobytes()
            self.pub_debug.publish(debug_msg)
        except Exception:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
