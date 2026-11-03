# dualsense.py — DualSense BLE HID Central driver for Pico W
# Connects to PS5 DualSense controller via BLE, parses HID input report.
#
# DualSense BLE HID report layout (input report ID 0x01, ~64 bytes):
#   Byte 0:  Left stick X  (0x00=left, 0x7F=center, 0xFF=right)
#   Byte 1:  Left stick Y  (0x00=up,   0x7F=center, 0xFF=down)
#   Byte 2:  Right stick X
#   Byte 3:  Right stick Y
#   Byte 4:  Buttons byte 1: bit0=square, bit1=cross(X), bit2=circle, bit3=triangle
#                             bit4=L1, bit5=R1, bit6=L2, bit7=R2
#   Byte 5:  Buttons byte 2: bit0=share, bit1=options, bit2=L3, bit3=R3
#                             bit4=PS, bit5=touchpad
#   Byte 6:  D-pad (0=N,1=NE,2=E,3=SE,4=S,5=SW,6=W,7=NW,8=none)
#
# NOTE: format verified from reverse engineering; may vary with firmware.
#       First connection prints raw bytes for calibration.

import uasyncio as asyncio
import gc

_DUALSENSE_NAME = "DualSense"
_HID_SERVICE    = 0x1812
_HID_REPORT     = 0x2A4D

# Joystick deadzone (center = 0x7F ± DEAD)
_DEAD = 30
_CENTER = 0x7F

class DualSense:
    def __init__(self):
        self.connected = False
        self.dy = 0        # -1=up, 0=center, 1=down
        self.dx = 0        # -1=left, 0=center, 1=right
        self.cross = False     # X button (jump/fire)
        self.square = False    # square button (restart)
        self.options = False   # options button
        self._raw = None       # last raw report for diagnostics
        self._debug = True     # print first report for calibration

    def _parse(self, data):
        if len(data) < 7:
            return
        if self._debug:
            print("[DS] raw:", list(data[:10]))
            self._debug = False

        lx = data[0]
        ly = data[1]

        # Joystick Y axis
        if ly < _CENTER - _DEAD:
            self.dy = -1
        elif ly > _CENTER + _DEAD:
            self.dy = 1
        else:
            self.dy = 0

        # Joystick X axis
        if lx < _CENTER - _DEAD:
            self.dx = -1
        elif lx > _CENTER + _DEAD:
            self.dx = 1
        else:
            self.dx = 0

        b1 = data[4]
        b2 = data[5]
        self.square  = bool(b1 & 0x01)
        self.cross   = bool(b1 & 0x02)
        self.options = bool(b2 & 0x02)

    async def run(self):
        """Infinite BLE scan-connect-read loop. Call as asyncio task."""
        try:
            import aioble
            import bluetooth
        except ImportError:
            print("[DS] BLE not available — DualSense disabled")
            return

        HID_SVC  = bluetooth.UUID(0x1812)
        HID_CHAR = bluetooth.UUID(0x2A4D)

        while True:
            self.connected = False
            self.dy = 0
            self.dx = 0
            self.cross = False
            self.square = False
            gc.collect()

            print("[DS] Scanning for DualSense...")
            try:
                device = None
                async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
                    async for result in scanner:
                        name = result.name()
                        if name and _DUALSENSE_NAME in name:
                            device = result.device
                            print(f"[DS] Found: {name} {result.device.addr_hex()}")
                            break

                if device is None:
                    print("[DS] Not found, retrying in 3s...")
                    await asyncio.sleep(3)
                    continue

                print("[DS] Connecting...")
                connection = await device.connect(timeout_ms=5000)
                print("[DS] Connected!")
                self.connected = True
                self._debug = True  # print first report after reconnect

                async with connection:
                    hid_service = await connection.service(HID_SVC)
                    if hid_service is None:
                        print("[DS] HID service not found")
                        continue

                    # Find the HID Report characteristic (may be multiple — take first)
                    report_char = await hid_service.characteristic(HID_CHAR)
                    if report_char is None:
                        print("[DS] HID report char not found")
                        continue

                    # Subscribe to notifications
                    await report_char.subscribe(notify=True)
                    print("[DS] Subscribed to HID reports")

                    while connection.is_connected():
                        try:
                            data = await report_char.notified(timeout_ms=1000)
                            if data:
                                self._parse(data)
                        except asyncio.TimeoutError:
                            pass  # normal, keep looping

                print("[DS] Disconnected")

            except Exception as e:
                print("[DS] Error:", e)
                await asyncio.sleep(2)
