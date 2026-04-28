from picamera2 import Picamera2, controls
import time

cam = Picamera2()

# Configura alla risoluzione massima
config = cam.create_still_configuration(
    main={"size": (1920, 1080), "format": "RGB888"},
    controls={
        # Disabilita AWB automatico (ingannato dall'IR)
        "AwbEnable": False,
        # Bilanciamento manuale: riduci rosso, aumenta blu
        # per compensare l'IR (valori da aggiustare)
        "ColourGains": (1.2, 2.0),  # (rosso, blu)
        # Esposizione automatica attiva
        "AeEnable": True,
    }
)
cam.configure(config)
cam.start()
time.sleep(2)  # attendi stabilizzazione

cam.capture_file("test_calibrato.jpg")
cam.stop()
cam.close()
print("Salvato: test_calibrato.jpg")

