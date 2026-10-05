"""
RoboArm – webové ovládání (Flask + pyserial), bez JavaScriptu.

Spuštění:
    pip install -r requirements.txt
    python app.py
a otevři http://127.0.0.1:5000
"""
import threading
import time
from collections import deque
from pathlib import Path

from flask import Flask, redirect, render_template, request, send_from_directory

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # bez pyserial funguje jen SIMULACE
    serial = None
    list_ports = None

ZAKLAD = Path(__file__).parent
BAUD = 9600
SIMULACE = "SIMULACE"

# ---------------------------------------------------------------------------
# Nastavení (uprav podle svého ramene)
# ---------------------------------------------------------------------------
LIMITY = {1: (0, 180), 2: (50, 130), 3: (0, 180), 4: (10, 170), 5: (0, 180)}  # min, max
KLESTE_OTEVRENO = 100
KLESTE_ZAVRENO = 60
VYCHOZI = {0: 130, 1: 100, 2: 150, 3: 0, 4: 180, 5: 70}  # jako loadPositions() v .ino


# ---------------------------------------------------------------------------
# Falešný port pro zkoušení bez Arduina
# ---------------------------------------------------------------------------
class FalesnySerial:
    def __init__(self):
        self.buf = deque()

    @property
    def in_waiting(self):
        return len(self.buf)

    def write(self, data):
        self.buf.append(b"OK: " + data)

    def readline(self):
        return self.buf.popleft() if self.buf else b""

    def close(self):
        pass


# ---------------------------------------------------------------------------
# Ovladač ramene
# ---------------------------------------------------------------------------
class Rameno:
    def __init__(self):
        self.ser = None
        self.port = None
        self.uhly = dict(VYCHOZI)
        self.log = deque(maxlen=15)
        self.zprava = None  # (kategorie, text) – zobrazí se jednou na stránce
        self.lock = threading.Lock()

    def zapis_log(self, text):
        self.log.appendleft(f"{time.strftime('%H:%M:%S')}  {text}")

    def cti(self):
        time.sleep(0.05)
        while self.ser.in_waiting:
            radek = self.ser.readline().decode(errors="replace").strip()
            if radek:
                self.zapis_log("← " + radek)

    def posli(self, text):
        if self.ser is None:
            raise RuntimeError("Arduino není připojeno.")
        self.ser.write((text + "\n").encode())
        self.zapis_log("→ " + text)
        self.cti()

    def pripojit(self, port):
        with self.lock:
            self.odpojit()
            if port == SIMULACE:
                self.ser = FalesnySerial()
            else:
                if serial is None:
                    raise RuntimeError("Chybí pyserial (pip install pyserial).")
                self.ser = serial.Serial(port, BAUD, timeout=0.2)
                time.sleep(2)  # Arduino se po otevření portu restartuje
                self.uhly = dict(VYCHOZI)
                self.cti()
            self.port = port
            self.zapis_log("Připojeno k " + port)

    def odpojit(self):
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None
        self.port = None

    def nastav(self, servo, uhel):
        with self.lock:
            self.posli(f"{servo} {uhel}")
            self.uhly[servo] = uhel

    def prikaz(self, znak):
        with self.lock:
            self.posli(znak)
            if znak == "r":
                self.uhly = dict(VYCHOZI)


rameno = Rameno()
app = Flask(__name__, template_folder=".", static_folder=None)  # index.html je šablona


def omez(servo, hodnota):
    lo, hi = LIMITY[servo]
    return max(lo, min(hi, int(hodnota)))


def najdi_porty():
    porty = []
    if list_ports is not None:
        porty = [(p.device, f"{p.device} – {p.description}") for p in list_ports.comports()]
    porty.append((SIMULACE, "SIMULACE (bez Arduina)"))
    return porty


def udelej(akce, ok=None):
    """Provede akci a uloží zprávu pro stránku, pak přesměruje zpět na Ovládání."""
    try:
        akce()
        rameno.zprava = ("ok", ok) if ok else None
    except Exception as e:
        rameno.zprava = ("chyba", str(e))
    return redirect("/#ovladani")


# ---------------------------------------------------------------------------
# Stránky a soubory (cesty stejné jako v HTML: ./style.css, ./foto/..., ...)
# ---------------------------------------------------------------------------
@app.route("/")
@app.route("/index.html")
def index():
    zprava, rameno.zprava = rameno.zprava, None
    return render_template(
        "index.html",
        kod=(ZAKLAD / "hotovy_kod.ino").read_text(encoding="utf-8"),
        uhly=rameno.uhly,
        log="\n".join(rameno.log) or "(zatím nic)",
        porty=najdi_porty(),
        pripojeno=rameno.ser is not None,
        port=rameno.port,
        disabled="" if rameno.ser is not None else "disabled",
        zprava=zprava,
    )


@app.route("/galerie.html")
def galerie():
    return send_from_directory(ZAKLAD, "galerie.html")


@app.route("/style.css")
def styl():
    return send_from_directory(ZAKLAD, "style.css")


@app.route("/hotovy_kod.ino")
def ino():
    return send_from_directory(ZAKLAD, "hotovy_kod.ino", as_attachment=True)


@app.route("/foto/<path:nazev>")
def foto(nazev):
    return send_from_directory(ZAKLAD / "foto", nazev)


@app.route("/zip-soubory/<path:nazev>")
def zip_soubory(nazev):
    return send_from_directory(ZAKLAD / "zip-soubory", nazev, as_attachment=True)


# ---------------------------------------------------------------------------
# Ovládání (formuláře)
# ---------------------------------------------------------------------------
@app.post("/pripojit")
def pripojit():
    return udelej(lambda: rameno.pripojit(request.form["port"]), "Připojeno.")


@app.post("/odpojit")
def odpojit():
    return udelej(rameno.odpojit, "Odpojeno.")


@app.post("/serva")
def serva():
    def akce():
        # odešle jen serva, jejichž posuvník se změnil
        for servo in LIMITY:
            pole = request.form.get(f"servo{servo}")
            if pole is None:
                continue
            uhel = omez(servo, pole)
            # posuvník neumí ukázat hodnotu mimo rozsah (např. výchozí 150° u serva 2)
            if uhel != omez(servo, rameno.uhly[servo]):
                rameno.nastav(servo, uhel)
        # tlačítka −5 / +5, např. "3:-5"
        krok = request.form.get("krok")
        if krok:
            servo, delta = (int(x) for x in krok.split(":"))
            rameno.nastav(servo, omez(servo, rameno.uhly[servo] + delta))

    return udelej(akce)


@app.post("/kleste/<akce>")
def kleste(akce):
    uhel = KLESTE_OTEVRENO if akce == "otevrit" else KLESTE_ZAVRENO
    return udelej(lambda: rameno.nastav(0, uhel))


@app.post("/prikaz/<znak>")
def prikaz(znak):
    if znak not in ("p", "r"):
        return "Neznámý příkaz", 404
    text = "Pozice uloženy do EEPROM." if znak == "p" else "Pozice resetovány."
    return udelej(lambda: rameno.prikaz(znak), text)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=False)