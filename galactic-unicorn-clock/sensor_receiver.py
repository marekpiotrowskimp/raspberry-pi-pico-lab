import uasyncio as asyncio
import usocket as socket
import json
import gc

UDP_PORT = 5000
_SEP = " "

_PM25_THRESHOLDS = [(35, (100, 255, 100)), (75, (255, 255, 100)), (9999, (255, 100, 100))]
_PM10_THRESHOLDS = [(50, (100, 255, 100)), (100, (255, 255, 100)), (9999, (255, 100, 100))]
_PM1_THRESHOLDS  = [(25, (100, 255, 100)), (50, (255, 255, 100)), (9999, (255, 100, 100))]


def _pm_color(value, thresholds):
    for limit, color in thresholds:
        if value <= limit:
            return color
    return (255, 100, 100)


class SensorReceiver:
    def __init__(self):
        self.devices = []
        self.last_update_ms = 0
        self._sock = None

    def has_data(self):
        return len(self.devices) > 0

    async def run(self):
        while True:
            try:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._sock.bind(('0.0.0.0', UDP_PORT))
                self._sock.setblocking(False)
                break
            except Exception as e:
                print("[SENSOR] Socket error:", e)
                await asyncio.sleep(5)

        print("[SENSOR] Listening on UDP port", UDP_PORT)

        while True:
            try:
                data_bytes, addr = self._sock.recvfrom(2048)
                if data_bytes:
                    data = json.loads(data_bytes.decode('utf-8'))
                    if data.get("type") == "air_quality_data" and "devices" in data:
                        self.devices = []
                        for dev in data["devices"]:
                            if dev.get("active", False):
                                self.devices.append({
                                    "name": dev.get("name", "?"),
                                    "temperature": dev.get("temperature", 0),
                                    "humidity": dev.get("humidity", 0),
                                    "pressure": dev.get("pressure", 0),
                                    "pm1_0": dev.get("pm1_0", 0),
                                    "pm2_5": dev.get("pm2_5", 0),
                                    "pm10": dev.get("pm10", 0),
                                })
                        self.last_update_ms = __import__("time").ticks_ms()
                        gc.collect()
            except OSError:
                pass
            except Exception as e:
                print("[SENSOR] Parse error:", e)
            await asyncio.sleep_ms(100)

    def get_segments(self, graphics):
        if not self.devices:
            return [], 0

        segments = []
        for i, dev in enumerate(self.devices):
            if i > 0:
                segments.append((_SEP, (100, 100, 100)))

            name = dev["name"][:6].upper()
            temp = "{:+.0f}C".format(dev["temperature"])
            hum  = "{:.0f}%".format(dev["humidity"])
            pres = "{:d}hPa".format(dev["pressure"])
            pm25 = "PM2.5:{}".format(dev["pm2_5"])
            pm1  = "PM1:{}".format(dev["pm1_0"])
            pm10 = "PM10:{}".format(dev["pm10"])

            segments.append((">" + name, (255, 255, 255)))
            segments.append((_SEP + temp, (255, 190, 30)))
            segments.append((_SEP + hum, (0, 200, 255)))
            segments.append((_SEP + pres, (255, 180, 100)))
            segments.append((_SEP + pm25, _pm_color(dev["pm2_5"], _PM25_THRESHOLDS)))
            segments.append((_SEP + pm1, _pm_color(dev["pm1_0"], _PM1_THRESHOLDS)))
            segments.append((_SEP + pm10, _pm_color(dev["pm10"], _PM10_THRESHOLDS)))

        graphics.set_font("bitmap14_outline")
        total = 0
        for text, _ in segments:
            total += graphics.measure_text(text, 1)

        return segments, total
