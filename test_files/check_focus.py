from picamera2 import Picamera2
import numpy as np
import time

cam = Picamera2()
config = cam.create_still_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={
        "AwbEnable": False,
        "ColourGains": (0.9, 1.1),
        "Sharpness": 3.0,
        "Contrast": 1.2,
        "Saturation": 1.3,
        "Brightness": 0.1,
    }
)
cam.configure(config)
cam.start()
time.sleep(2)

def laplacian_variance(img):
    # Converti in grayscale
    gray = np.mean(img, axis=2)
    # Kernel Laplaciano
    kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]])
    # Applica convoluzione manuale su una patch centrale
    h, w = gray.shape
    cx, cy = h//2, w//2
    patch = gray[cx-100:cx+100, cy-100:cy+100]
    score = np.var(patch)
    return score

print("Ruota l'obiettivo e premi INVIO per misurare la nitidezza (Ctrl+C per uscire)")
i = 0
while True:
    input(f"  Scatto {i+1}: premi INVIO...")
    frame = cam.capture_array()
    score = laplacian_variance(frame)
    filename = f"focus_{i:02d}_score{int(score)}.jpg"
    cam.capture_file(filename)
    print(f"  → Nitidezza: {score:.1f} (più alto = più a fuoco) - {filename}")
    i += 1

cam.stop()
cam.close()
