#!/usr/bin/env python3
"""
Test flusso video locale — mostra il flusso OV5647 in una finestra OpenCV.
Premi Q per uscire.
"""
from picamera2 import Picamera2
import cv2 as cv
import time

print("Inizializzazione camera OV5647...")
cam = Picamera2()
config = cam.create_video_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
cam.configure(config)
cam.start()
time.sleep(1)

print("Flusso video avviato — premi Q per uscire")
m_fps = 0
t_start = time.time()

while True:
    frame = cam.capture_array()
    frame_bgr = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

    m_fps += 1
    fps = m_fps / (time.time() - t_start)
    cv.putText(frame_bgr, f"FPS: {fps:.1f}", (10, 25),
               cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 0), 2)

    cv.imshow("OV5647 Test", frame_bgr)
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cam.stop()
cv.destroyAllWindows()
print("Test completato.")
