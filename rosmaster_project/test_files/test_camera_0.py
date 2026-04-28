from picamera2 import Picamera2
import time

cam = Picamera2()

config = cam.create_still_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={
        "AwbEnable": True,
        "ColourGains": (0.9, 1.1),  # più rosso, meno blu
        "AeEnable": True,
        "Sharpness": 3.0,	   # Più nitidezza
        "Contrast": 1.2,           # Aumenta il contrasto
    	'Saturation': 1.3,         # Colori più vivaci
    	'Brightness': 0.1,         # Leggermente più luminoso
    	
    }
)
cam.configure(config)
cam.start()
time.sleep(2)

cam.capture_file("test_ir2.jpg")
cam.stop()
cam.close()
print("Salvato: test_ir2.jpg")
