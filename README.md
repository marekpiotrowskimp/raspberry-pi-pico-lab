# raspberry-pi-pico-lab

A collection of **Raspberry Pi Pico / Pico W** projects (MicroPython).

| Directory | Project |
|---|---|
| [`weather-station/`](weather-station/) | Weather station: DHT, pressure, PMS7003 dust sensor, LCD / ST7789 display, Wi-Fi (ESP-AT) |
| [`weather-server/`](weather-server/) | Server collecting the station's readings (Python, SQLite) |
| [`galactic-unicorn-clock/`](galactic-unicorn-clock/) | Clock on a Pimoroni Galactic Unicorn: NTP, weather (Open-Meteo), automatic brightness, a mini-game with a DualSense gamepad |
| [`epaper-ble-frame/`](epaper-ble-frame/) | 7.5" e-paper frame — images sent over BLE / Wi-Fi |
| [`tufty-games/`](tufty-games/) | Games and demos for the Pimoroni Tufty 2040 |
| [`arkanoid/`](arkanoid/) | Arkanoid on an ST7789 display |

## Wi-Fi configuration

Projects that use Wi-Fi read the network credentials from `secrets.py` (git-ignored):

```sh
cp galactic-unicorn-clock/secrets_example.py galactic-unicorn-clock/secrets.py
```

Upload to the Pico: `mpremote cp *.py :` in the project directory.

`tufty-games`: `Game2.py` and `retro_badge.py` display a 320×240 JPEG (`eggs.jpg`, `squirrel.jpg`) — upload your own file with that name.

The e-paper driver (`epaper-ble-frame/epaper750.py`) comes from the Waveshare examples (license in the file header).

## License

MIT — see [LICENSE](LICENSE).
