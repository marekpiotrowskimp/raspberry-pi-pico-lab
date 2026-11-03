# raspberry-pi-pico-lab

Zbiór projektów na **Raspberry Pi Pico / Pico W** (MicroPython).

| Katalog | Projekt |
|---|---|
| [`weather-station/`](weather-station/) | Stacja pogodowa: DHT, ciśnienie, pyłomierz PMS7003, LCD / ST7789, Wi-Fi (ESP-AT) |
| [`weather-server/`](weather-server/) | Serwer zbierający pomiary stacji (Python, SQLite) |
| [`galactic-unicorn-clock/`](galactic-unicorn-clock/) | Zegar na Pimoroni Galactic Unicorn: NTP, pogoda (Open-Meteo), automatyczna jasność, mini-gra z padem DualSense |
| [`epaper-ble-frame/`](epaper-ble-frame/) | Ramka e-paper 7,5" — obrazy przesyłane przez BLE / Wi-Fi |
| [`tufty-games/`](tufty-games/) | Gry i demka na Pimoroni Tufty 2040 |
| [`arkanoid/`](arkanoid/) | Arkanoid na wyświetlaczu ST7789 |

## Konfiguracja Wi-Fi

Projekty z Wi-Fi czytają dane sieci z `secrets.py` (w `.gitignore`):

```sh
cp galactic-unicorn-clock/secrets_example.py galactic-unicorn-clock/secrets.py
```

Wgrywanie na Pico: `mpremote cp *.py :` w katalogu projektu.

`tufty-games`: `Game2.py` i `retro_badge.py` wyświetlają obraz JPEG 320×240 (`eggs.jpg`, `squirrel.jpg`) — wgraj własny plik o tej nazwie.

Sterownik e-paper (`epaper-ble-frame/epaper750.py`) pochodzi z przykładów Waveshare (licencja w nagłówku pliku).
