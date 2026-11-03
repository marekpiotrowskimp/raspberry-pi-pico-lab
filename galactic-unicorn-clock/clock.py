import time
import network
import ntptime
import urequests
from machine import RTC
from galactic import GalacticUnicorn
import sounds
import quotes
import sensor_receiver

# Wi-Fi networks — tried in round-robin order
from secrets import WIFI_NETWORKS  # patrz secrets_example.py

# Retry settings
WIFI_CONNECT_TIMEOUT = 20   # seconds to wait for connection (weak signal needs more time)
WIFI_RETRY_DELAY = 2        # seconds between retries

# Weather API — Open-Meteo, no key required
WEATHER_URL = (
    "http://api.open-meteo.com/v1/forecast"
    "?latitude=53.12&longitude=18.00"
    "&current=temperature_2m,weather_code,wind_speed_10m"
    ",relative_humidity_2m,surface_pressure"
    "&hourly=precipitation_probability"
    "&forecast_hours=12"
    "&timezone=Europe%2FWarsaw"
)
WEATHER_INTERVAL = 600      # refresh weather every 10 minutes (seconds)
QUOTE_REFRESH_INTERVAL = 15 * 60   # refresh quote every 15 minutes (seconds)

# Display timing
CLOCK_DURATION = 15_000     # ms — how long to show clock before weather scroll (matches ~13s music)

# WMO weather code → description
WMO_LABELS = {
    0:  "BEZCHMURNIE",
    1:  "POGODNIE",   2: "CZESCIOWE ZACHMURZENIE", 3: "POCHMURNO",
    45: "MGLA",       48: "MGLA",
    51: "MZAWKA",     53: "MZAWKA",     55: "MZAWKA",
    56: "MZAWKA",     57: "MZAWKA",
    61: "DESZCZ",     63: "DESZCZ",     65: "SILNY DESZCZ",
    66: "DESZCZ",     67: "SILNY DESZCZ",
    71: "SNIEG",      73: "SNIEG",      75: "SILNY SNIEG", 77: "SNIEG",
    80: "PRZELOTNY DESZCZ", 81: "PRZELOTNY DESZCZ", 82: "PRZELOTNY DESZCZ",
    85: "SNIEG",      86: "SILNY SNIEG",
    95: "BURZA",      96: "BURZA",      99: "BURZA",
}

graphics = None
galactic = None
sound = None
rtc = RTC()

# Weather data
weather_temp = None
weather_label = None
weather_wind = None
weather_humidity = None
weather_pressure = None
weather_rain_prob = None
weather_last_update = -(WEATHER_INTERVAL * 1000)  # force fetch on first draw

# Quote data
_quote_text = None
_quote_author = None
_quote_last_update = -(QUOTE_REFRESH_INTERVAL * 1000)  # force fetch on first draw
_quote_segments = []
_quote_width = 0

# Sensor data
_sensor_receiver = None
_sensor_segments = []
_sensor_width = 0

# Scroll state
_mode = "clock"
_next_after_clock = "weather"   # cycles: "weather" / "quote" / "sensor"
_clock_start = 0
_scroll_x = 0               # integer pixels — no jitter
_scroll_segments = []       # list of (text, (r, g, b)) to draw
_scroll_width = 0           # total pixel width of all segments
_SCROLL_FRAME_MS = 50       # target frame time ms (20fps)

# Intro scroll state
_intro_stop_x = 0           # _scroll_x value at which intro stops (time segment at X=0)
_intro_prefix_width = 0     # pixel width of day+date prefix (segments before time)


_WEEKDAYS = ("PON", "WT", "SR", "CZW", "PT", "SOB", "ND")


def show_status(text, r=55, g=55, b=55):
    graphics.set_font("bitmap6")
    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()
    graphics.set_pen(graphics.create_pen(r, g, b))
    graphics.text(text, 2, 2, -1, 1)
    galactic.update(graphics)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    time.sleep(1)

    known_ssids = {ssid: pwd for ssid, pwd in WIFI_NETWORKS}

    while True:
        # scan and pick known network with best RSSI
        show_status("SKAN", 55, 55, 0)
        try:
            nets = wlan.scan()
        except Exception:
            nets = []

        best_ssid = None
        best_rssi = -999
        best_pwd = None
        for n in nets:
            try:
                ssid = n[0].decode("utf-8")
            except Exception:
                continue
            if ssid in known_ssids and n[3] > best_rssi:
                best_ssid = ssid
                best_rssi = n[3]
                best_pwd = known_ssids[ssid]

        if best_ssid is None:
            print("No known network found, retrying scan...")
            time.sleep(2)
            continue

        print("Best network: {} rssi:{}".format(best_ssid, best_rssi))
        show_status("WIFI", 55, 55, 0)
        wlan.connect(best_ssid, best_pwd)
        for _ in range(WIFI_CONNECT_TIMEOUT):
            if wlan.isconnected():
                break
            time.sleep(1)
        if wlan.isconnected():
            print("Connected to {}:".format(best_ssid), wlan.ifconfig())
            return wlan
        print("Connect failed (status {}), rescanning...".format(wlan.status()))
        show_status("RETRY", 55, 0, 0)
        wlan.disconnect()
        time.sleep(2)


def sync_ntp():
    attempt = 0
    while True:
        attempt += 1
        try:
            ntptime.settime()
            print("NTP synced:", rtc.datetime())
            return
        except Exception as e:
            print("NTP attempt {} failed: {}".format(attempt, e))
            show_status("NTP {}".format(attempt), 55, 30, 0)
            time.sleep(3)


def _build_scroll_segments():
    """Build _scroll_segments and _scroll_width from current weather globals."""
    global _scroll_segments, _scroll_width

    sep = " "  # gap between fields

    segments = [
        (weather_temp,                   (255, 190,  30)),  # yellow — like clock
        (sep + weather_label,            (255, 255, 255)),  # white
        (sep + weather_wind,             (100, 180, 255)),  # blue
        (sep + weather_humidity,         (  0, 200, 255)),  # cyan
        (sep + weather_pressure,         (180, 180, 180)),  # grey
        (sep + weather_rain_prob,  (100, 255, 100)),  # green
    ]

    graphics.set_font("bitmap14_outline")
    total = 0
    for text, _ in segments:
        total += graphics.measure_text(text, 1)

    _scroll_segments = segments
    _scroll_width = total


def _build_quote_segments():
    """Build _quote_segments and _quote_width from current quote globals."""
    global _quote_segments, _quote_width

    if not _quote_text:
        return

    text_part = _quote_text + "  \x14 " + _quote_author + "   "
    # \x14 is em-dash in bitmap14_outline; use " - " if not supported
    text_part = _quote_text + "  - " + _quote_author + "   "

    segments = [
        (text_part, (180, 130, 255)),  # lavender
    ]

    graphics.set_font("bitmap14_outline")
    total = 0
    for text, _ in segments:
        total += graphics.measure_text(text, 1)

    _quote_segments = segments
    _quote_width = total


def _build_sensor_segments():
    global _sensor_segments, _sensor_width
    global _sensor_receiver
    if _sensor_receiver is None or not _sensor_receiver.has_data():
        _sensor_segments = []
        _sensor_width = 0
        return
    _sensor_segments, _sensor_width = _sensor_receiver.get_segments(graphics)


def fetch_quote_data():
    global _quote_text, _quote_author, _quote_last_update
    text, author = quotes.fetch_quote()
    _quote_text = text
    _quote_author = author
    _quote_last_update = time.ticks_ms()
    _build_quote_segments()


def fetch_weather():
    global weather_temp, weather_label, weather_wind
    global weather_humidity, weather_pressure, weather_rain_prob
    global weather_last_update

    try:
        r = urequests.get(WEATHER_URL, timeout=10)
        data = r.json()
        r.close()

        c = data["current"]
        temp     = c["temperature_2m"]
        code     = int(c["weather_code"])
        wind     = c["wind_speed_10m"]
        humidity = int(c["relative_humidity_2m"])
        pressure = int(c["surface_pressure"])

        # max precipitation probability over next 12 hours
        probs = data["hourly"]["precipitation_probability"]
        rain_prob = max(probs) if probs else 0

        weather_temp      = "{:+.0f}C".format(temp)
        weather_label     = WMO_LABELS.get(code, "???")
        weather_wind      = "{:.0f}KM/H".format(wind)
        weather_humidity  = "{:.0f}%".format(float(humidity))
        weather_pressure  = "{:.0f}HPA".format(float(pressure))
        weather_rain_prob = "DESZCZ {:.0f}%".format(float(rain_prob))

        weather_last_update = time.ticks_ms()
        print("Weather: {} {} {} {} {} {}".format(
            weather_temp, weather_label, weather_wind,
            weather_humidity, weather_pressure, weather_rain_prob))

    except Exception as e:
        print("Weather fetch failed:", e)
        if weather_temp is None:
            weather_temp      = "BRAK"
            weather_label     = "DANYCH"
            weather_wind      = ""
            weather_humidity  = ""
            weather_pressure  = ""
            weather_rain_prob = ""

    _build_scroll_segments()


def last_sunday(year, month):
    for day in range(31, 24, -1):
        try:
            weekday = time.localtime(time.mktime((year, month, day, 0, 0, 0, 0, 0)))[6]
            if weekday == 6:
                return day
        except:
            continue
    return 31


def is_dst_poland(year, month, day, hour):
    if month < 3 or month > 10:
        return False
    elif 3 < month < 10:
        return True
    elif month == 3:
        return (day > last_sunday(year, 3)) or \
               (day == last_sunday(year, 3) and hour >= 2)
    elif month == 10:
        return (day < last_sunday(year, 10)) or \
               (day == last_sunday(year, 10) and hour < 3)
    return False


def draw_clock():
    year, month, day, weekday, local_hour, minute, second = _get_local_time()

    graphics.set_font("bitmap14_outline")
    graphics.set_pen(graphics.create_pen(255, 190, 30))

    graphics.text("{:02d}".format(local_hour), 0, -2, 0, 1)
    graphics.text("{:02d}.{:02d}".format(minute, second), 18, -2, 0, 1)

    if second % 2 == 0:
        graphics.pixel(16, 3)
        graphics.pixel(16, 4)
        graphics.pixel(16, 6)
        graphics.pixel(16, 7)


@micropython.native  # noqa: F821
def draw_weather_scroll():
    """Draw one frame of slow weather scroll. Returns True when done."""
    global _scroll_x

    graphics.set_font("bitmap14_outline")

    cx = _scroll_x
    for seg_text, (r, g, b) in _scroll_segments:
        w = graphics.measure_text(seg_text, 1)
        if cx + w > 0 and cx < GalacticUnicorn.WIDTH:
            graphics.set_pen(graphics.create_pen(r, g, b))
            graphics.text(seg_text, cx, -2, -1, 1)
        cx += w

    _scroll_x -= 1

    return _scroll_x < -_scroll_width


@micropython.native  # noqa: F821
def draw_quote_scroll():
    """Draw one frame of quote scroll. Returns True when done."""
    global _scroll_x

    graphics.set_font("bitmap14_outline")

    cx = _scroll_x
    for seg_text, (r, g, b) in _quote_segments:
        w = graphics.measure_text(seg_text, 1)
        if cx + w > 0 and cx < GalacticUnicorn.WIDTH:
            graphics.set_pen(graphics.create_pen(r, g, b))
            graphics.text(seg_text, cx, -2, -1, 1)
        cx += w

    _scroll_x -= 1

    return _scroll_x < -_quote_width


@micropython.native
def draw_sensor_scroll():
    global _scroll_x
    graphics.set_font("bitmap14_outline")
    cx = _scroll_x
    for seg_text, (r, g, b) in _sensor_segments:
        w = graphics.measure_text(seg_text, 1)
        if cx + w > 0 and cx < GalacticUnicorn.WIDTH:
            graphics.set_pen(graphics.create_pen(r, g, b))
            graphics.text(seg_text, cx, -2, -1, 1)
        cx += w
    _scroll_x -= 1
    return _scroll_x < -_sensor_width


def _get_local_time():
    """Return (year, month, day, weekday, local_hour, minute, second)."""
    dt = rtc.datetime()
    year, month, day, _, hour, minute, second, _ = dt
    offset = 2 if is_dst_poland(year, month, day, hour) else 1
    local_hour = (hour + offset) % 24
    # rtc weekday: 0=Mon..6=Sun
    weekday = dt[3]
    return year, month, day, weekday, local_hour, minute, second


def _start_intro():
    """Prepare intro scroll: build prefix width, set _scroll_x and _intro_stop_x."""
    global _scroll_x, _intro_prefix_width, _intro_stop_x
    year, month, day, weekday, local_hour, minute, second = _get_local_time()

    day_str  = _WEEKDAYS[weekday] + " "
    date_str = "{:02d}.{:02d}.{}  ".format(day, month, year)

    graphics.set_font("bitmap14_outline")
    prefix_w = graphics.measure_text(day_str, 1) + graphics.measure_text(date_str, 1)

    _intro_prefix_width = prefix_w
    _scroll_x = GalacticUnicorn.WIDTH
    # intro stops when time segment reaches X=0, i.e. scroll_x == -prefix_w
    _intro_stop_x = -prefix_w


def draw_intro_scroll():
    """Draw one frame of intro scroll (day + date + live time). Returns True when stopped."""
    global _scroll_x

    year, month, day, weekday, local_hour, minute, second = _get_local_time()

    day_str  = _WEEKDAYS[weekday] + " "
    date_str = "{:02d}.{:02d}.{}  ".format(day, month, year)

    graphics.set_font("bitmap14_outline")

    stopped = _scroll_x <= _intro_stop_x

    if stopped:
        # rysuj czas identycznie jak draw_clock() — zero glitcha przy przejściu
        graphics.set_pen(graphics.create_pen(255, 190, 30))
        graphics.text("{:02d}".format(local_hour), 0, -2, 0, 1)
        graphics.text("{:02d}.{:02d}".format(minute, second), 18, -2, 0, 1)
        if second % 2 == 0:
            graphics.pixel(16, 3)
            graphics.pixel(16, 4)
            graphics.pixel(16, 6)
            graphics.pixel(16, 7)
    else:
        # scroll — dzień i data jako prefix, czas rysowany jak draw_clock() z offsetem cx
        cx = _scroll_x
        for seg_text, (r, g, b) in [
            (day_str,  (200, 200, 200)),
            (date_str, (150, 150, 150)),
        ]:
            w = graphics.measure_text(seg_text, 1)
            if cx + w > 0 and cx < GalacticUnicorn.WIDTH:
                graphics.set_pen(graphics.create_pen(r, g, b))
                graphics.text(seg_text, cx, -2, -1, 1)
            cx += w
        # czas — identyczny rendering jak draw_clock() ale z offsetem cx
        graphics.set_pen(graphics.create_pen(255, 190, 30))
        graphics.text("{:02d}".format(local_hour), cx + 0, -2, 0, 1)
        graphics.text("{:02d}.{:02d}".format(minute, second), cx + 18, -2, 0, 1)
        if second % 2 == 0:
            graphics.pixel(cx + 16, 3)
            graphics.pixel(cx + 16, 4)
            graphics.pixel(cx + 16, 6)
            graphics.pixel(cx + 16, 7)
        _scroll_x -= 1

    return stopped


def is_night_hours():
    """Returns True between 22:00 and 06:00 local time."""
    _, _, _, _, local_hour, _, _ = _get_local_time()
    return local_hour >= 22 or local_hour < 6


def init():
    global sound, _clock_start

    connect_wifi()
    sync_ntp()

    graphics.set_font("bitmap14_outline")
    sound = sounds.Sounds(galactic)

    fetch_weather()
    fetch_quote_data()
    _clock_start = time.ticks_ms()


def draw():
    global _mode, _next_after_clock, _clock_start, _scroll_x

    now = time.ticks_ms()

    graphics.set_pen(graphics.create_pen(0, 0, 0))
    graphics.clear()

    # music triggers — independent of display mode
    dt = rtc.datetime()
    _minute = dt[5]
    _second = dt[6]
    _night = is_night_hours()

    if _minute == 0 and _second == 0:
        if not _night:
            _mode = "clock"
            _clock_start = now
            sound.play()
        else:
            sound.stop_play()

    if _minute == 0 and _second == 13:
        sound.stop_play()

    if _minute == 30 and _second == 0 and not _night:
        sound.beep()

    if _mode == "clock":
        # fetch weather only during clock mode, and only after 5s cooldown after mode switch
        if time.ticks_diff(now, _clock_start) > 5000:
            if time.ticks_diff(now, weather_last_update) >= WEATHER_INTERVAL * 1000:
                fetch_weather()
            if time.ticks_diff(now, _quote_last_update) >= QUOTE_REFRESH_INTERVAL * 1000:
                fetch_quote_data()
            _build_sensor_segments()
        draw_clock()
        if time.ticks_diff(now, _clock_start) >= CLOCK_DURATION:
            _mode = _next_after_clock
            if _next_after_clock == "weather":
                _next_after_clock = "quote"
            elif _next_after_clock == "quote":
                _next_after_clock = "sensor" if (_sensor_receiver and _sensor_receiver.has_data()) else "weather"
            else:
                _next_after_clock = "weather"
            _scroll_x = GalacticUnicorn.WIDTH
        galactic.update(graphics)
        time.sleep(0.015)

    elif _mode == "weather":
        t0 = time.ticks_ms()
        done = draw_weather_scroll()
        galactic.update(graphics)
        if done:
            _start_intro()
            _mode = "intro"
        else:
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            if elapsed < _SCROLL_FRAME_MS:
                time.sleep_ms(_SCROLL_FRAME_MS - elapsed)

    elif _mode == "quote":
        if not _quote_segments:
            # no quote yet — skip to intro
            _start_intro()
            _mode = "intro"
            return
        t0 = time.ticks_ms()
        done = draw_quote_scroll()
        galactic.update(graphics)
        if done:
            _start_intro()
            _mode = "intro"
        else:
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            if elapsed < _SCROLL_FRAME_MS:
                time.sleep_ms(_SCROLL_FRAME_MS - elapsed)

    elif _mode == "sensor":
        if not _sensor_segments or not (_sensor_receiver and _sensor_receiver.has_data()):
            _start_intro()
            _mode = "intro"
            return
        t0 = time.ticks_ms()
        done = draw_sensor_scroll()
        galactic.update(graphics)
        if done:
            _start_intro()
            _mode = "intro"
        else:
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            if elapsed < _SCROLL_FRAME_MS:
                time.sleep_ms(_SCROLL_FRAME_MS - elapsed)

    elif _mode == "intro":
        t0 = time.ticks_ms()
        stopped = draw_intro_scroll()
        galactic.update(graphics)
        if stopped:
            _mode = "clock"
            _clock_start = time.ticks_ms()
        else:
            elapsed = time.ticks_diff(time.ticks_ms(), t0)
            if elapsed < _SCROLL_FRAME_MS:
                time.sleep_ms(_SCROLL_FRAME_MS - elapsed)
