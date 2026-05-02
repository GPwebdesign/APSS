#!/usr/bin/env python3
"""
APSS — Validatore pacchetti TCP Yahboom
Costruisce, verifica e decodifica pacchetti senza robot fisico.

Uso:
    python3 validate.py                          # menu interattivo
    python3 validate.py "$021a0c000000000028#"   # verifica pacchetto singolo
"""

import sys

CAR_TYPE = 0x02  # X3_PLUS Mecanum — fisso per APSS

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

def checksum(payload: list) -> int:
    return sum(payload) % 256


def to_byte(val: int) -> int:
    """Signed int (-100..+100) -> unsigned byte (complemento a 2)."""
    val = max(-100, min(100, val))
    return val & 0xFF


def build_cmd(cmd_id: int, length: int, data: list) -> str:
    """
    length: valore esatto del byte len nel protocollo Yahboom (NON calcolato da len(data)).
    Valori verificati: 0x0F->0x04, 0x1A->0x0C, 0x11->0x06, 0x10->0x08
    """
    payload = [CAR_TYPE, cmd_id, length] + data
    cs = checksum(payload)
    hex_str = "".join(f"{b:02x}" for b in payload)
    return f"${hex_str}{cs:02x}#"


def verify(packet: str) -> dict:
    """Verifica un pacchetto Yahboom. Ritorna dict con valid, decoded, ecc."""
    packet = packet.strip()
    if not (packet.startswith("$") and packet.endswith("#")):
        return {"valid": False, "error": "Formato non valido: deve iniziare con $ e finire con #"}

    inner = packet[1:-1]
    if len(inner) < 8 or len(inner) % 2 != 0:
        return {"valid": False, "error": f"Lunghezza payload non valida: {len(inner)} chars"}

    payload_hex = inner[:-2]
    cs_hex = inner[-2:]

    try:
        payload_bytes = [int(payload_hex[i:i+2], 16) for i in range(0, len(payload_hex), 2)]
        actual_cs = int(cs_hex, 16)
    except ValueError as e:
        return {"valid": False, "error": f"Hex non valido: {e}"}

    expected_cs = checksum(payload_bytes)
    valid = expected_cs == actual_cs

    return {
        "valid": valid,
        "payload_bytes": payload_bytes,
        "expected_cs": expected_cs,
        "actual_cs": actual_cs,
        "decoded": decode(payload_bytes),
    }


def decode(payload: list) -> dict:
    """Decodifica i byte del payload in campi leggibili."""
    if len(payload) < 3:
        return {"error": "Payload troppo corto"}

    car_type = payload[0]
    cmd_id   = payload[1]
    length   = payload[2]
    data     = payload[3:]

    result = {
        "car_type": f"0x{car_type:02X}",
        "cmd":      f"0x{cmd_id:02X}",
        "len":      f"0x{length:02X} ({length})",
        "data_bytes": [f"0x{b:02X}" for b in data],
    }

    if cmd_id == 0x0F:
        result["desc"] = "INIT — imposta car_type e g_mode"
        if data:
            result["g_mode"] = data[0]

    elif cmd_id == 0x1A:
        result["desc"] = "SET_MOTOR — controllo 4 motori diretto"
        if len(data) >= 4:
            def from_byte(b):
                return b if b < 128 else b - 256
            result["M1_ant_sx"]  = from_byte(data[0])
            result["M2_ant_dx"]  = from_byte(data[1])
            result["M3_post_sx"] = from_byte(data[2])
            result["M4_post_dx"] = from_byte(data[3])

    elif cmd_id == 0x11:
        result["desc"] = "SERVO_PWM — controllo servo singolo"
        if len(data) >= 2:
            servo_id = data[0]
            angle    = data[1]
            name = {1: "S1=Tilt", 2: "S2=Pan"}.get(servo_id, f"id={servo_id}")
            result["servo"] = f"{name} -> {angle}deg (0x{angle:02X})"

    elif cmd_id == 0x10:
        result["desc"] = "MOVE_BASE — movimento base (legacy, preferire 0x1A)"
        if len(data) >= 2:
            result["num_x"] = data[0]
            result["num_y"] = data[1]

    else:
        result["desc"] = f"Comando sconosciuto: 0x{cmd_id:02X}"

    return result


# ---------------------------------------------------------------------------
# Costruttori — length verificata sui pacchetti reali
# ---------------------------------------------------------------------------

def build_init() -> str:
    return build_cmd(0x0F, 0x04, [0x01])


def build_stop() -> str:
    return build_cmd(0x1A, 0x0C, [0x00, 0x00, 0x00, 0x00, 0x00])


def build_motor(m1: int, m2: int, m3: int, m4: int) -> str:
    data = [to_byte(m1), to_byte(m2), to_byte(m3), to_byte(m4), 0x00]
    return build_cmd(0x1A, 0x0C, data)


def build_mecanum(vx: float, vy: float, vz: float, speed: int = 60) -> str:
    """
    Cinematica Mecanum APSS.
    vx=avanti(+)/indietro(-), vy=destra(+)/sinistra(-), vz=orario(+)/antiorario(-)
    speed: velocita base 0-100
    """
    m1 = int((vx - vy + vz) * speed)
    m2 = int((vx + vy - vz) * speed)
    m3 = int((vx + vy + vz) * speed)
    m4 = int((vx - vy - vz) * speed)
    return build_motor(m1, m2, m3, m4)


def build_servo(servo_id: int, angle: int) -> str:
    """servo_id: 1=Tilt, 2=Pan — angle: 0-180"""
    angle = max(0, min(180, angle))
    return build_cmd(0x11, 0x06, [servo_id, angle])


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_verify(packet: str):
    result = verify(packet)
    print(f"\nPacchetto: {packet}")
    if not result["valid"]:
        print(f"  ERRORE: {result.get('error', 'checksum non valido')}")
        if "expected_cs" in result:
            print(f"  Checksum atteso: 0x{result['expected_cs']:02x} — ricevuto: 0x{result['actual_cs']:02x}")
        return
    print(f"  Checksum OK (0x{result['actual_cs']:02x})")
    d = result["decoded"]
    for k, v in d.items():
        if k not in ("error",):
            print(f"  {k}: {v}")


def print_build(label: str, packet: str):
    print(f"\n{label}")
    print(f"  Pacchetto: {packet}")
    r = verify(packet)
    d = r.get("decoded", {})
    for k, v in d.items():
        if k not in ("car_type", "cmd", "len", "data_bytes"):
            print(f"  {k}: {v}")


# ---------------------------------------------------------------------------
# Menu interattivo
# ---------------------------------------------------------------------------

MENU = """
============================================
  APSS > Validatore pacchetti TCP Yahboom
============================================
  1. Verifica pacchetto esistente
  2. Costruisci: Init
  3. Costruisci: Stop
  4. Costruisci: Movimento Mecanum (vx, vy, vz)
  5. Costruisci: Servo (id, angolo)
  6. Costruisci: Motori diretti (M1 M2 M3 M4)
  7. Pacchetti fissi di riferimento
  q. Quit
"""


def menu():
    while True:
        print(MENU)
        scelta = input("Scelta: ").strip().lower()

        if scelta == "1":
            pkt = input("  Pacchetto (es. $021a0c000000000028#): ").strip()
            print_verify(pkt)

        elif scelta == "2":
            print_build("INIT", build_init())

        elif scelta == "3":
            print_build("STOP", build_stop())

        elif scelta == "4":
            try:
                vx  = float(input("  vx avanti/indietro (-1.0..+1.0): "))
                vy  = float(input("  vy laterale (-1.0..+1.0): "))
                vz  = float(input("  vz rotazione (-1.0..+1.0): "))
                spd = int(input("  speed base (default 60): ") or "60")
                print_build(f"MECANUM vx={vx} vy={vy} vz={vz} speed={spd}",
                            build_mecanum(vx, vy, vz, spd))
            except ValueError:
                print("  Valore non valido.")

        elif scelta == "5":
            try:
                sid = int(input("  servo id (1=Tilt, 2=Pan): "))
                ang = int(input("  angolo (0-180): "))
                print_build(f"SERVO id={sid} angle={ang}", build_servo(sid, ang))
            except ValueError:
                print("  Valore non valido.")

        elif scelta == "6":
            try:
                m1 = int(input("  M1 ant.sx (-100..+100): "))
                m2 = int(input("  M2 ant.dx (-100..+100): "))
                m3 = int(input("  M3 post.sx (-100..+100): "))
                m4 = int(input("  M4 post.dx (-100..+100): "))
                print_build(f"MOTOR M1={m1} M2={m2} M3={m3} M4={m4}",
                            build_motor(m1, m2, m3, m4))
            except ValueError:
                print("  Valore non valido.")

        elif scelta == "7":
            print()
            print_build("INIT",              build_init())
            print_build("STOP",              build_stop())
            print_build("AVANTI speed=60",   build_mecanum(1.0,  0.0, 0.0, 60))
            print_build("INDIETRO speed=60", build_mecanum(-1.0, 0.0, 0.0, 60))
            print_build("ROT DX speed=60",   build_mecanum(0.0,  0.0, 1.0, 60))
            print_build("PAN HOME 100deg",   build_servo(2, 100))
            print_build("TILT HOME 95deg",   build_servo(1, 95))

        elif scelta == "q":
            break

        input("\n  Invio per continuare...")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print_verify(sys.argv[1])
    else:
        menu()
