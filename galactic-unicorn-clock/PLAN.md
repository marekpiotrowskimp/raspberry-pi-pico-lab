# Galactic Unicorn Clock — dokumentacja projektu

## Cel
Zegar cyfrowy na Pimoroni Galactic Unicorn (Raspberry Pi Pico W) z:
- synchronizacją czasu przez NTP
- polską strefą czasową (DST)
- scrollującą pogodą (Open-Meteo)
- auto-brightness z czujnika światła
- muzyką o pełnej godzinie

## Urządzenie
- **Hardware:** Pimoroni Galactic Unicorn, matryca 53×11 px
- **Firmware:** MicroPython Pimoroni
- **Port:** `/dev/cu.usbmodem1301`
- **Overclock:** 200 MHz

## Pliki projektu

| Plik | Opis |
|---|---|
| `main.py` | Punkt wejścia: auto-brightness, offset jasności, pętla główna |
| `clock.py` | Zegar, Wi-Fi, NTP, pogoda, scroll |
| `sounds.py` | 5-kanałowy syntezator, muzyka godzinowa |
| `PLAN.md` | Ten dokument |

## Konfiguracja

### Wi-Fi
- Sieci Wi-Fi: w `secrets.py` (wzór: `secrets_example.py`)
- Retry w nieskończoność z feedbackiem na ekranie (`RETRY X`)

### Pogoda
- Provider: Open-Meteo (darmowe, bez klucza API)
- Lokalizacja: Bydgoszcz (`lat=53.12, lon=18.00`)
- Odświeżanie: co 10 minut
- Dane: temperatura / zachmurzenie / wiatr / wilgotność / ciśnienie / deszcz 12h

### Wyświetlanie
- Font zegara: `bitmap14_outline`, `y=-2`
- Font scrollu: `bitmap14_outline`, `y=-2`
- Zegar wyświetlany przez 10s, potem scroll pogody
- Scroll: 1px/klatkę, 50ms/klatkę (~20px/s)

### Auto-brightness
- Czujnik: `galactic.light()`, mapowanie `10–295 → 0.1–1.0`
- Offset użytkownika: `±0.9`, zapisywany do `/offset.json` przy zwolnieniu klawisza
- Klawisze: `BRIGHTNESS_UP` / `BRIGHTNESS_DOWN`

## Segmenty scrollu pogody

| Segment | Kolor |
|---|---|
| Temperatura (`+20C`) | żółty `(255, 190, 30)` |
| Zachmurzenie | biały `(255, 255, 255)` |
| Wiatr (`KM/H`) | niebieski `(100, 180, 255)` |
| Wilgotność (`%`) | cyjan `(0, 200, 255)` |
| Ciśnienie (`HPA`) | szary `(180, 180, 180)` |
| Deszcz 12h (`DESZCZ X%`) | zielony `(100, 255, 100)` |

## Kluczowe decyzje techniczne

- `fetch_weather()` wywoływany tylko w trybie zegara (nie podczas scrollu) z 5s cooldownem po przełączeniu trybu — eliminuje zamrożenie scrollu przez HTTP request
- Timing klatki scrollu: `t0 = ticks_ms()` na początku klatki, `sleep_ms(_SCROLL_FRAME_MS - elapsed)` po `galactic.update()`, tylko gdy `not done` — eliminuje opóźnienie między scrollem a zegarem
- Warunek końca scrollu: `_scroll_x < -_scroll_width` — tekst kończy się dokładnie gdy ostatni piksel opuści lewą krawędź
- `galactic.update()` wywoływany tylko w `clock.py` (nie w `main.py`)
- Wi-Fi/NTP: retry w nieskończoność (bez fallback)
- DST Polska: automatyczne wykrywanie ostatniej niedzieli marca/października
- `sounds.py`: usunięto błędną deklarację `global beat` z metody `next_beat()`

## Architektura przepływu

```
main.py — pętla główna
  ↓
effect.draw()  (clock.py)
  ├── _mode == "clock"
  │     ├── fetch_weather() jeśli >10min i >5s od startu trybu
  │     ├── draw_clock()
  │     └── przełącz na "weather" po CLOCK_DURATION (10s)
  └── _mode == "weather"
        ├── draw_weather_scroll()
        ├── galactic.update()
        ├── sleep do 50ms (tylko gdy scroll trwa)
        └── przełącz na "clock" gdy scroll zakończony
```

## Historia zmian

### Faza 1 — Cleanup
- Usunięto zbędne pliki: `fire.py`, `supercomputer.py`, `rainbow.py`, `retroprompt.py`, `sound.py`, `scroll.py`, `light_sensor.py`
- Uproszczono `main.py`: usunięto menu efektów, dodano auto-brightness z offsetem
- `graphics.py` przemianowany na `clock.py`
- Naprawiono bug `global beat` w `sounds.py`

### Faza 2 — Funkcjonalność
- Dodano Wi-Fi retry z feedbackiem na ekranie
- Dodano NTP retry
- Dodano DST Polska
- Dodano scrollującą pogodę z Open-Meteo
- 6 segmentów pogody w różnych kolorach

### Faza 3 — Optymalizacja scrollu
- Usunięto podwójny `galactic.update()` (był w `main.py` i `clock.py`)
- Przeniesiono `fetch_weather()` do bloku `clock` — scroll nigdy nie jest przerywany przez HTTP
- Timer-based frame pacing: dokładne 50ms/klatkę
- Usunięto `@micropython.native` z funkcji używających globals (powodował błędy)
- Poprawiono warunek końca scrollu — wyeliminowano 2.6s czarną przerwę przed zegarem
- Sleep tylko gdy scroll trwa — natychmiastowe przejście do zegara po zakończeniu scrollu
