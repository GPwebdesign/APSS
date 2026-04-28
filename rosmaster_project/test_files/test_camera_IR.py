from picamera2 import Picamera2, controls
import time

cam = Picamera2()

config = cam.create_still_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={
        "AwbEnable": False,      # disabilita AWB automatico (ingannato dall'IR)
        "ColourGains": (1.2, 2.0),  # (rosso, blu) - compensa dominante IR
        "AeEnable": True,        # esposizione automatica attiva
        "Sharpness": 2.0,        # aumenta nitidezza
        "Contrast": 1.2,         # aumenta contrasto
    }
)
cam.configure(config)
cam.start()
time.sleep(2)  # attendi stabilizzazione AE

cam.capture_file("test_ir.jpg")
cam.stop()
cam.close()
print("Salvato: test_ir.jpg")