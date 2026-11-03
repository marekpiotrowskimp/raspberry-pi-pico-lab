import machine, gc, time
import uasyncio as asyncio
import json
from galactic import GalacticUnicorn
from picographics import PicoGraphics, DISPLAY_GALACTIC_UNICORN as DISPLAY

# Overclock to 200 MHz
machine.freq(200_000_000)

galactic = GalacticUnicorn()
graphics = PicoGraphics(DISPLAY)

# Splash screen
graphics.set_font("bitmap6")
graphics.set_pen(graphics.create_pen(0, 0, 0))
graphics.clear()
graphics.set_pen(graphics.create_pen(55, 55, 55))
graphics.text("LOADING...", 4, 2, -1, 1)
galactic.update(graphics)

import clock as clock_mod
from sounds import Sounds
from sensor_receiver import SensorReceiver

clock_mod.graphics = graphics
clock_mod.galactic = galactic
clock_mod.init()

sounds = Sounds(galactic)
clock_mod.sounds = sounds

sensor_recv = SensorReceiver()
clock_mod._sensor_receiver = sensor_recv

# ---- Auto-brightness ----
MIN_LS  = 10
MAX_LS  = 295
MIN_BR  = 0.1
MAX_BR  = 1.0
TRANS   = 1.0 / 72.0
OFFSET_FILE = '/offset.json'

def load_offset():
    try:
        with open(OFFSET_FILE) as f:
            return float(json.load(f).get('offset', 0.0))
    except:
        return 0.0

def save_offset(value):
    try:
        with open(OFFSET_FILE, 'w') as f:
            json.dump({'offset': value}, f)
    except:
        pass

offset     = load_offset()
brightness = MIN_BR
_was_sleep = False
_was_up    = False
_was_down  = False
_sleep_mode = False
_night_override_until = 0  # ticks_ms until which night override is active

NIGHT_OVERRIDE_MS = 30 * 60 * 1000  # 30 minutes
NIGHT_BRIGHTNESS  = 0.02

async def app_task():
    global offset, brightness, _was_sleep, _was_up, _was_down, _sleep_mode
    global _night_override_until

    while True:
        sleep_p = galactic.is_pressed(GalacticUnicorn.SWITCH_SLEEP)
        if sleep_p and not _was_sleep:
            _sleep_mode = not _sleep_mode
        _was_sleep = sleep_p

        if _sleep_mode:
            galactic.set_brightness(max(0.0, galactic.get_brightness() - 0.05))
            if galactic.get_brightness() > 0.0:
                clock_mod.draw()
            await asyncio.sleep_ms(33)
            continue

        now_ms = time.ticks_ms()
        night = clock_mod.is_night_hours()
        override_active = night and time.ticks_diff(_night_override_until, now_ms) > 0

        up_p   = galactic.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_UP)
        down_p = galactic.is_pressed(GalacticUnicorn.SWITCH_BRIGHTNESS_DOWN)
        if up_p:
            offset = min(0.9, offset + 0.05)
            if night:
                _night_override_until = time.ticks_add(now_ms, NIGHT_OVERRIDE_MS)
        elif _was_up:
            save_offset(offset)
        if down_p:
            offset = max(-0.9, offset - 0.05)
            if night:
                _night_override_until = time.ticks_add(now_ms, NIGHT_OVERRIDE_MS)
        elif _was_down:
            save_offset(offset)
        _was_up   = up_p
        _was_down = down_p

        if night and not override_active:
            galactic.set_brightness(NIGHT_BRIGHTNESS)
        else:
            raw    = galactic.light()
            target = (raw - MIN_LS) * (MAX_BR - MIN_BR) / (MAX_LS - MIN_LS) + MIN_BR + offset
            target = max(MIN_BR, min(MAX_BR, target))
            brightness += (target - brightness) * TRANS
            galactic.set_brightness(brightness)

        clock_mod.draw()

        await asyncio.sleep_ms(1)

async def main():
    gc.collect()
    asyncio.create_task(app_task())
    asyncio.create_task(sensor_recv.run())
    while True:
        await asyncio.sleep(10)

asyncio.run(main())
