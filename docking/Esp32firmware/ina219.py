# ina219.py — driver INA219 per MicroPython
# Corrente positiva = flusso da VIN+ verso VIN- (ricarica batteria)
# HW-831B: VIN+ ← sorgente (XH-M603 BAT+), VIN- → carico (pogo pin +)

_REG_CONFIG      = 0x00
_REG_SHUNT_V     = 0x01
_REG_BUS_V       = 0x02
_REG_CURRENT     = 0x04
_REG_CALIBRATION = 0x05

# Configurazione default: 32V, gain /8, 12bit, continuous shunt+bus
_CONFIG_DEFAULT  = 0x399F

class INA219:
    def __init__(self, i2c, address=0x40, shunt_ohms=0.1):
        self._i2c         = i2c
        self._addr        = address
        self._shunt       = shunt_ohms
        self._current_lsb = 0.0

    def configura(self, max_amps=3.0):
        """Imposta calibrazione per la corrente massima attesa."""
        self._current_lsb = max_amps / 32768
        cal = int(0.04096 / (self._current_lsb * self._shunt))
        self._write(_REG_CALIBRATION, cal)
        self._write(_REG_CONFIG, _CONFIG_DEFAULT)

    def tensione_v(self):
        """Tensione bus (lato VIN-) in Volt."""
        raw = self._read(_REG_BUS_V)
        return round(((raw >> 3) * 4) / 1000.0, 3)

    def corrente_a(self):
        """Corrente in Ampere.
        Positiva = ricarica attiva (XH-M603 eroga corrente verso batteria).
        Negativa = flusso inverso (batteria alimenta XH-M603 a relay aperto).
        Segno dal raw senza inversione — verificato sul cablaggio fisico HW-831B."""
        raw = self._read(_REG_CURRENT)
        if raw > 32767:
            raw -= 65536
        return round(raw * self._current_lsb, 4)

    def potenza_w(self):
        """Potenza calcolata: V * I."""
        return round(self.tensione_v() * self.corrente_a(), 3)

    def leggi_tutto(self):
        """Restituisce dict con v, a, w in una sola chiamata."""
        v = self.tensione_v()
        a = self.corrente_a()
        return {"v": v, "a": a, "w": round(v * a, 3)}

    def ok(self):
        """Verifica presenza sensore sul bus I2C."""
        try:
            self._read(_REG_BUS_V)
            return True
        except:
            return False

    def _write(self, reg, val):
        self._i2c.writeto(
            self._addr,
            bytes([reg, (val >> 8) & 0xFF, val & 0xFF])
        )

    def _read(self, reg):
        self._i2c.writeto(self._addr, bytes([reg]))
        d = self._i2c.readfrom(self._addr, 2)
        return (d[0] << 8) | d[1]
