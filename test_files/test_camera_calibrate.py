#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Camera Calibration Tool
Regola i parametri della camera in tempo reale e salva in camera_params.json
Tasti:
  R/r = ColourGains rosso +/-0.1
  B/b = ColourGains blu +/-0.1
  S/s = Sharpness +/-0.5
  C/c = Contrast +/-0.1
  T/t = Saturation +/-0.1
  +/- = Brightness +/-0.1
  E   = toggle AeEnable
  W   = toggle AwbEnable
  P   = switch profilo streaming/vision
  INVIO = salva entrambi i profili in camera_params.json
  Q   = esci senza salvare
"""
from picamera2 import Picamera2, controls
import cv2 as cv
import json
import os
import time

params_streaming = {
    "AwbEnable":   True,
    "ColourGains": [1.0, 1.0],
    "AeEnable":    True,
    "Sharpness":   2.0,
    "Contrast":    1.0,
    "Brightness":  0.0,
    "Saturation":  1.2,
}

params_vision = {
    "AwbEnable":   True,
    "ColourGains": [1.0, 1.0],
    "AeEnable":    True,
    "Sharpness":   3.0,
    "Contrast":    1.1,
    "Brightness":  0.1,
    "Saturation":  0.3,
}

current_profile = "streaming"
params = params_streaming.copy()

OUTPUT_JSON = os.path.join(os.path.dirname(__file__),
                           '..', 'camera_params.json')

def apply_params(cam, p):
    try:
        cam.set_controls({
            "AwbEnable":   p["AwbEnable"],
            "ColourGains": tuple(p["ColourGains"]),
            "AeEnable":    p["AeEnable"],
            "Sharpness":   p["Sharpness"],
            "Contrast":    p["Contrast"],
            "Brightness":  p["Brightness"],
            "Saturation":  p["Saturation"],
        })
        time.sleep(0.5)
    except Exception as e:
        print(f"[WARN] {e}")

def print_params(p):
    print(f"\nParamentri attuali:")
    print(f"  ColourGains R={p['ColourGains'][0]:.1f}  B={p['ColourGains'][1]:.1f}")
    print(f"  Sharpness={p['Sharpness']:.1f}  Contrast={p['Contrast']:.1f}")
    print(f"  Brightness={p['Brightness']:.1f}  Saturation={p['Saturation']:.1f}")
    print(f"  AwbEnable={p['AwbEnable']}  AeEnable={p['AeEnable']}")

cam = Picamera2()
config = cam.create_video_configuration(
    main={"size": (640, 480), "format": "RGB888"},
    controls={})
cam.configure(config)
cam.start()
time.sleep(1)
apply_params(cam, params)
time.sleep(1)

print("Camera calibration avviata. Premi i tasti per regolare.")
print(f"[PROFILE] Profilo attivo: {current_profile}")
print_params(params)

while True:
    frame = cam.capture_array()
    frame_bgr = cv.cvtColor(frame, cv.COLOR_RGB2BGR)

    # Info a schermo
    cv.putText(frame_bgr,
        f"R:{params['ColourGains'][0]:.1f} B:{params['ColourGains'][1]:.1f}",
        (10, 25), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
    cv.putText(frame_bgr,
        f"Sharp:{params['Sharpness']:.1f} Cont:{params['Contrast']:.1f} Sat:{params['Saturation']:.1f}",
        (10, 50), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
    cv.putText(frame_bgr,
        f"AWB:{params['AwbEnable']} AE:{params['AeEnable']}",
        (10, 75), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
    cv.putText(frame_bgr,
        f"Profile: {current_profile}",
        (10, 100), cv.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
    cv.putText(frame_bgr,
        "P=switch  INVIO=salva  Q=esci",
        (10, 460), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

    cv.imshow("APSS Camera Calibration", frame_bgr)

    key = cv.waitKey(30) & 0xFF
    changed = False

    if   key == ord('q'): break
    elif key == 13:  # INVIO
        output = {
            "streaming": params_streaming,
            "vision": params_vision
        }
        with open(OUTPUT_JSON, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nEntrambi i profili salvati in {OUTPUT_JSON}")
        break
    elif key == ord('P'):
        if current_profile == "streaming":
            current_profile = "vision"
            params = params_vision.copy()
        else:
            current_profile = "streaming"
            params = params_streaming.copy()
        apply_params(cam, params)
        print(f"[PROFILE] Switched to: {current_profile}")
        print_params(params)
    elif key == ord('R'): params['ColourGains'][0] = round(params['ColourGains'][0]+0.1, 1); changed=True
    elif key == ord('r'): params['ColourGains'][0] = round(params['ColourGains'][0]-0.1, 1); changed=True
    elif key == ord('B'): params['ColourGains'][1] = round(params['ColourGains'][1]+0.1, 1); changed=True
    elif key == ord('b'): params['ColourGains'][1] = round(params['ColourGains'][1]-0.1, 1); changed=True
    elif key == ord('S'): params['Sharpness']  = round(params['Sharpness']+0.5,  1); changed=True
    elif key == ord('s'): params['Sharpness']  = round(params['Sharpness']-0.5,  1); changed=True
    elif key == ord('C'): params['Contrast']   = round(params['Contrast']+0.1,   1); changed=True
    elif key == ord('c'): params['Contrast']   = round(params['Contrast']-0.1,   1); changed=True
    elif key == ord('T'): params['Saturation'] = round(params['Saturation']+0.1, 1); changed=True
    elif key == ord('t'): params['Saturation'] = round(params['Saturation']-0.1, 1); changed=True
    elif key == ord('+'): params['Brightness'] = round(params['Brightness']+0.1, 1); changed=True
    elif key == ord('-'): params['Brightness'] = round(params['Brightness']-0.1, 1); changed=True
    elif key == ord('E'): params['AeEnable']  = not params['AeEnable'];  changed=True
    elif key == ord('W'): params['AwbEnable'] = not params['AwbEnable']; changed=True

    if changed:
        if current_profile == "streaming":
            params_streaming.update(params)
        else:
            params_vision.update(params)
        apply_params(cam, params)
        print_params(params)

cam.stop()
cv.destroyAllWindows()
