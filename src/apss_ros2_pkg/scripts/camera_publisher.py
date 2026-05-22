#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from picamera2 import Picamera2
import time
import json
import os

_CAMERA_PARAMS_JSON = os.path.join(
    os.path.expanduser("~"), "Workspaces/rosmaster_project/camera_params.json")

_VISION_DEFAULTS = {
    "AwbEnable":   False,
    "ColourGains": (0.9, 1.1),
    "AeEnable":    True,
    "Sharpness":   3.0,
    "Contrast":    1.2,
    "Saturation":  1.3,
    "Brightness":  0.1,
}

def _load_vision_params():
    try:
        with open(_CAMERA_PARAMS_JSON) as f:
            p = json.load(f)['vision']
        return {
            "AwbEnable":   p.get("AwbEnable",   _VISION_DEFAULTS["AwbEnable"]),
            "ColourGains": tuple(p.get("ColourGains", _VISION_DEFAULTS["ColourGains"])),
            "AeEnable":    p.get("AeEnable",    _VISION_DEFAULTS["AeEnable"]),
            "Sharpness":   p.get("Sharpness",   _VISION_DEFAULTS["Sharpness"]),
            "Contrast":    p.get("Contrast",    _VISION_DEFAULTS["Contrast"]),
            "Saturation":  p.get("Saturation",  _VISION_DEFAULTS["Saturation"]),
            "Brightness":  p.get("Brightness",  _VISION_DEFAULTS["Brightness"]),
        }
    except Exception:
        return _VISION_DEFAULTS

class CameraPublisher(Node):
    def __init__(self):
        super().__init__("camera_publisher_node")
        self.pub = self.create_publisher(Image, "image_raw", 10)
        self.bridge = CvBridge()

        self.cam = Picamera2()
        config = self.cam.create_video_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            controls=_load_vision_params()
        )
        self.cam.configure(config)
        self.cam.start()
        time.sleep(2)  # attendi stabilizzazione AE

        self.timer = self.create_timer(0.033, self.publish_frame)  # ~30 FPS
        self.get_logger().info("Camera Publisher Node avviato!")

    def publish_frame(self):
        frame = self.cam.capture_array()
        msg = self.bridge.cv2_to_imgmsg(frame, encoding="rgb8")
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "camera"
        self.pub.publish(msg)

    def destroy_node(self):
        self.cam.stop()
        self.cam.close()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    print("Camera Publisher Node Running...")
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print("Terminating Node...")
        node.destroy_node()

if __name__ == '__main__':
    main()
