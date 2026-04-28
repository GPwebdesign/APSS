# test_files/test_rplidar_viz.py
# APSS — Autonomous Patrol and Surveillance System
# Test standalone visualizzazione RPLIDAR A1M8
#
# Verifica: LiDAR operativo su /dev/ttyUSB1
# Nota hardware: il LiDAR è montato con offset fisico di 90°
#   → il "davanti" del robot corrisponde a 90° nel sistema di riferimento LiDAR
#   → questo offset sarà compensato nel tf/URDF in fase di integrazione ROS2
#
# Output: polar plot in tempo reale — aggiornamento ogni 100ms
# Colori: rosso = ostacolo vicino, verde = ostacolo lontano (range max 4m)
#
# Uso: python3 test_files/test_rplidar_viz.py
# Richiede: pip3 install rplidar-roboticia matplotlib

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from rplidar import RPLidar

# --- Configurazione ---
PORT = '/dev/ttyUSB1'       # Porta seriale LiDAR (ttyUSB0 = scheda Yahboom)
MAX_RANGE_MM = 4000         # Range massimo visualizzato: 4000mm = 4m
UPDATE_INTERVAL_MS = 100    # Intervallo aggiornamento plot in millisecondi

# --- Inizializzazione LiDAR ---
lidar = RPLidar(PORT, baudrate=115200)
scan_data = []

# --- Setup polar plot ---
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
ax.set_title('APSS — RPLIDAR A1M8 Live Scan\n(Nord = fronte robot)', va='bottom')

# ###0° puntato verso il "Nord" del plot = direzione visiva intuitiva###
# Offset +90° compensa il montaggio fisico del LiDAR:
# il fronte del robot corrisponde a 90° nel sistema di riferimento LiDAR nativo.
# Con offset=90 il fronte robot punta sempre verso la cima del plot (Nord visivo).
ax.set_theta_zero_location('N', offset=90)
# Senso orario — coerente con il verso di rotazione del LiDAR A1M8
ax.set_theta_direction(-1)
# Range massimo visualizzato
ax.set_rlim(0, MAX_RANGE_MM)
# Label distanza in mm
ax.set_ylabel('mm', labelpad=30)

scatter = ax.scatter([], [], s=2, c='cyan')

# --- Funzione di aggiornamento frame ---
def update(frame):
    """
    Chiamata da FuncAnimation ad ogni frame.
    Legge il prossimo scan dal LiDAR e aggiorna il plot.
    Ogni punto ha formato: (qualità, angolo_gradi, distanza_mm)
    NOTA: l'angolo NON viene compensato dell'offset 90° qui —
          la visualizzazione rispecchia il sistema di riferimento LiDAR nativo.
          La compensazione avverrà nel tf ROS2.
    """
    global scan_data
    try:
        scan_data = next(scan_iter)
    except Exception:
        return scatter,

    angles = np.radians([p[1] for p in scan_data])
    distances = [p[2] for p in scan_data]

    # Colore proporzionale alla distanza: rosso=vicino, giallo=medio, verde=lontano
    colors = plt.cm.RdYlGn([d / MAX_RANGE_MM for d in distances])

    scatter.set_offsets(np.column_stack([angles, distances]))
    scatter.set_color(colors)
    return scatter,

# --- Avvio scansione e animazione ---
scan_iter = lidar.iter_scans()

ani = animation.FuncAnimation(
    fig,
    update,
    interval=UPDATE_INTERVAL_MS,
    blit=True,
    cache_frame_data=False
)

try:
    plt.show()
finally:
    # Sempre eseguito — anche in caso di chiusura finestra o Ctrl+C
    lidar.stop()
    lidar.disconnect()
    print("LiDAR disconnesso.")