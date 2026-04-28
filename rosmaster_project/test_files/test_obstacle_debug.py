"""
APSS — Test visivo obstacle detector
Mostra la ROI e i contorni rilevati in tempo reale.
Premi Q=esci, +/-=Canny low threshold, A/Z=min_area, U/D=roi_top, R=reset valori
"""
import sys
sys.path.insert(0, '/usr/lib/python3.10')
from servo_init import servo_home
from picamera2 import Picamera2
import cv2 as cv
import numpy as np

servo_home()
cam = Picamera2()
cam.configure(cam.create_video_configuration(
    main={"size": (640, 480), "format": "RGB888"}))
cam.start()

roi_top   = 0.75
threshold = 60
min_area  = 4000

PERSISTENCE        = 3
persist_count      = 0
last_direction     = 'none'
confirmed_direction = 'none'

print("Tasti: Q=esci, +/-=Canny low threshold, A/Z=min_area, U/D=roi_top, R=reset")
print(f"Valori iniziali: threshold={threshold}, min_area={min_area}, roi_top={roi_top}")

while True:
    frame = cam.capture_array()
    frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
    h, w  = frame.shape[:2]
    roi_y = int(h * roi_top)

    roi   = frame[roi_y:h, 0:w]
    gray  = cv.cvtColor(roi, cv.COLOR_BGR2GRAY)
    blur  = cv.GaussianBlur(gray, (5, 5), 0)
    edges = cv.Canny(blur, threshold, threshold*2)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (15, 15))
    binary = cv.dilate(edges, kernel, iterations=2)

    contours, _ = cv.findContours(
        binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    valid = [c for c in contours if cv.contourArea(c) > min_area]

    # Linea ROI
    cv.line(frame, (0, roi_y), (w, roi_y), (0, 255, 0), 2)
    cv.putText(frame, "ROI", (5, roi_y - 5),
               cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    # Terzi verticali
    third = w // 3
    cv.line(frame, (third,   roi_y), (third,   h), (255, 255, 0), 1)
    cv.line(frame, (2*third, roi_y), (2*third, h), (255, 255, 0), 1)
    cv.putText(frame, "L", (third//2,        roi_y+20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)
    cv.putText(frame, "C", (third+third//2,  roi_y+20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)
    cv.putText(frame, "R", (2*third+third//2,roi_y+20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

    # Contorni validi
    for c in valid:
        x, y, cw, ch = cv.boundingRect(c)
        cv.rectangle(frame, (x, roi_y+y), (x+cw, roi_y+y+ch), (0, 0, 255), 2)

    # Info
    direction = "none"
    if valid:
        left   = sum(1 for c in valid if cv.boundingRect(c)[0] < third)
        right  = sum(1 for c in valid if cv.boundingRect(c)[0]+cv.boundingRect(c)[2] > 2*third)
        center = sum(1 for c in valid if not (cv.boundingRect(c)[0] > 2*third or cv.boundingRect(c)[0]+cv.boundingRect(c)[2] < third))
        if len(valid) >= 3 or (left > 0 and right > 0):
            direction = "full"
        elif center > 0 and left == 0 and right == 0:
            direction = "center"
        elif left > right:
            direction = "left"
        elif right > left:
            direction = "right"
        else:
            direction = "center"

    # Persistence filter
    if direction != 'none':
        if direction == last_direction:
            persist_count = min(persist_count + 1, PERSISTENCE)
        else:
            persist_count = 1
        last_direction = direction
    else:
        persist_count = max(persist_count - 1, 0)
        if persist_count == 0:
            last_direction = 'none'

    confirmed_direction = last_direction if persist_count >= PERSISTENCE else 'none'

    color_dir = (0, 0, 255) if confirmed_direction != "none" else (0, 255, 0)
    cv.putText(frame, f"thresh:{threshold} area:{min_area} roi:{roi_top:.2f}",
               (10, 25), cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv.putText(frame, f"contours:{len(valid)} dir:{confirmed_direction}",
               (10, 52), cv.FONT_HERSHEY_SIMPLEX, 0.6, color_dir, 2)

    cv.imshow("APSS Obstacle Debug", frame)
    cv.imshow("Binary ROI", binary)

    key = cv.waitKey(1) & 0xFF
    if   key == ord('q'): break
    elif key == ord('+'): threshold = min(255, threshold+5);  print(f"threshold={threshold}")
    elif key == ord('-'): threshold = max(0,   threshold-5);  print(f"threshold={threshold}")
    elif key == ord('a'): min_area += 500;                    print(f"min_area={min_area}")
    elif key == ord('z'): min_area  = max(100, min_area-500); print(f"min_area={min_area}")
    elif key == ord('u'): roi_top = min(0.95, roi_top+0.05);  print(f"roi_top={roi_top:.2f}")
    elif key == ord('d'): roi_top = max(0.10, roi_top-0.05);  print(f"roi_top={roi_top:.2f}")
    elif key == ord('r'): threshold=60; min_area=4000; roi_top=0.75; print("Reset valori")

cam.stop()
cv.destroyAllWindows()
print(f"\nValori finali: threshold={threshold}, min_area={min_area}, roi_top={roi_top:.2f}")
print("Aggiorna obstacle_detector_node.py con questi valori!")
