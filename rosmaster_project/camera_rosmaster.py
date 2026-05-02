##!/usr/bin/env python3
# coding=utf-8
import cv2 as cv
import time
import numpy as np
import json
import os

# V4.2.0 — Aggiunto supporto camera CSI OV5647 tramite picamera2 
class Rosmaster_Camera(object):

    def __init__(self, video_id=0, width=640, height=480, debug=False):
        self.__debug = debug
        self.__video_id = int(video_id)
        self.__state = False
        self.__width = width
        self.__height = height
        self.__picam = None  # usato solo per TYPE_CSI_CAMERA

        self.TYPE_DEPTH_CAMERA      = 0x50
        self.TYPE_USB_CAMERA        = 0x51
        self.TYPE_WIDE_ANGLE_CAMERA = 0x52
        self.TYPE_CSI_CAMERA        = 0x53  # OV5647 via picamera2

        if self.__video_id == self.TYPE_CSI_CAMERA:
            self.__init_csi_camera()
        elif self.__video_id == self.TYPE_DEPTH_CAMERA:
            self.__video = cv.VideoCapture('/dev/camera_depth')
            if self.__debug: print("video:camera_depth")
            self.__finalize_init()
        elif self.__video_id == self.TYPE_USB_CAMERA:
            self.__video = cv.VideoCapture('/dev/camera_usb')
            if self.__debug: print("video:camera_usb")
            self.__finalize_init()
        elif self.__video_id == self.TYPE_WIDE_ANGLE_CAMERA:
            self.__video = cv.VideoCapture('/dev/camera_wide_angle')
            if self.__debug: print("video:camera_wide_angle")
            self.__finalize_init()
        else:
            self.__video = cv.VideoCapture(self.__video_id)
            if self.__debug: print("video:", self.__video_id)
            self.__finalize_init()

    def __load_streaming_params(self):
        """Legge il profilo 'streaming' da camera_params.json, fallback su valori hardcoded."""
        defaults = {
            "AwbEnable":   True,
            "ColourGains": (1.3, 1.4),
            "AeEnable":    True,
            "Sharpness":   2.0,
            "Contrast":    1.1,
            "Saturation":  0.8,
            "Brightness":  0.0,
        }
        json_path = os.path.join(os.path.dirname(__file__), 'camera_params.json')
        try:
            with open(json_path) as f:
                p = json.load(f)['streaming']
            return {
                "AwbEnable":   p.get("AwbEnable",   defaults["AwbEnable"]),
                "ColourGains": tuple(p.get("ColourGains", defaults["ColourGains"])),
                "AeEnable":    p.get("AeEnable",    defaults["AeEnable"]),
                "Sharpness":   p.get("Sharpness",   defaults["Sharpness"]),
                "Contrast":    p.get("Contrast",    defaults["Contrast"]),
                "Saturation":  p.get("Saturation",  defaults["Saturation"]),
                "Brightness":  p.get("Brightness",  defaults["Brightness"]),
            }
        except Exception:
            if self.__debug:
                print("[camera] camera_params.json non trovato — uso valori default")
            return defaults

    def __init_csi_camera(self):
        """Inizializza la camera CSI OV5647 tramite picamera2"""
        try:
            from picamera2 import Picamera2
            self.__picam = Picamera2()
            config = self.__picam.create_video_configuration(
                main={"size": (self.__width, self.__height), "format": "RGB888"},
                controls=self.__load_streaming_params()
            )
            self.__picam.configure(config)
            self.__picam.start()
            time.sleep(2)  # attendi stabilizzazione AE
            self.__state = True
            if self.__debug:
                print("---------CSI Camera OV5647 Init OK!------------")
        except Exception as e:
            self.__state = False
            if self.__debug:
                print(f"---------CSI Camera Init Error: {e}------------")

    def __finalize_init(self):
        """Verifica apertura e configura camera USB/V4L2"""
        success = self.__video.isOpened()
        if not success:
            if self.__debug:
                print("---------Camera Init Error!------------")
            return
        self.__state = True
        self.__config_camera()
        if self.__debug:
            print("---------Video:0x%02x Init OK!------------" % self.__video_id)

    def __del__(self):
        if self.__debug:
            print("---------Del Camera!------------")
        if self.__picam is not None:
            try:
                self.__picam.stop()
                self.__picam.close()
            except Exception:
                pass
        elif hasattr(self, '_Rosmaster_Camera__video'):
            self.__video.release()
        self.__state = False

    def __config_camera(self):
        cv_edition = cv.__version__
        if cv_edition[0] == '3':
            self.__video.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'XVID'))
        else:
            self.__video.set(cv.CAP_PROP_FOURCC, cv.VideoWriter.fourcc('M', 'J', 'P', 'G'))
        self.__video.set(cv.CAP_PROP_FRAME_WIDTH,  self.__width)
        self.__video.set(cv.CAP_PROP_FRAME_HEIGHT, self.__height)

    def isOpened(self):
        if self.__picam is not None:
            return self.__state
        return self.__video.isOpened()

    def clear(self):
        if self.__picam is not None:
            try:
                self.__picam.stop()
                self.__picam.close()
            except Exception:
                pass
            self.__picam = None
        elif self.isOpened():
            self.__video.release()
        self.__state = False

    def reconnect(self):
        self.clear()
        if self.__video_id == self.TYPE_CSI_CAMERA:
            self.__init_csi_camera()
            return self.__state
        elif self.__video_id == self.TYPE_DEPTH_CAMERA:
            self.__video = cv.VideoCapture('/dev/camera_depth')
        elif self.__video_id == self.TYPE_USB_CAMERA:
            self.__video = cv.VideoCapture('/dev/camera_usb')
        elif self.__video_id == self.TYPE_WIDE_ANGLE_CAMERA:
            self.__video = cv.VideoCapture('/dev/camera_wide_angle')
        else:
            self.__video = cv.VideoCapture(self.__video_id)
        success, _ = self.__video.read()
        if not success:
            self.__state = False
            if self.__debug:
                print("---------Camera Reconnect Error!------------")
            return False
        self.__state = True
        self.__config_camera()
        if self.__debug:
            print("---------Video:0x%02x Reconnect OK!------------" % self.__video_id)
        return True

    def get_frame(self):
        """Restituisce (success, frame_bgr)"""
        if self.__picam is not None:
            try:
                frame_rgb = self.__picam.capture_array()
                return True, frame_rgb
            except Exception as e:
                if self.__debug:
                    print(f"CSI get_frame error: {e}")
                return False, bytes({1})
        success, image = self.__video.read()
        if not success:
            return success, bytes({1})
        return success, image

    def get_frame_jpg(self, text="", color=(0, 255, 0)):
        """Restituisce (success, jpeg_bytes)"""
        success, image = self.get_frame()
        if not success:
            return success, bytes({1})
        if text != "":
            cv.putText(image, str(text), (10, 20),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        success, jpeg = cv.imencode('.jpg', image)
        return success, jpeg.tobytes()


if __name__ == '__main__':
    camera = Rosmaster_Camera(video_id=0x53, debug=True)
    t_start = time.time()
    m_fps = 0
    while camera.isOpened():
        ret, frame = camera.get_frame()
        if not ret:
            break
        m_fps += 1
        fps = m_fps / (time.time() - t_start)
        cv.putText(frame, f"FPS:{int(fps)}", (20, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.9, (0, 200, 0), 1)
        cv.imshow('frame', frame)
        if cv.waitKey(1) & 0xFF in (27, ord('q')):
            break
    del camera
    cv.destroyAllWindows()