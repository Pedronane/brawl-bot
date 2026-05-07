# brawl-bot

Bot Python per Brawl Stars su BlueStacks (Windows).
Screen capture + CV2 → input WASD/mouse. Anti-ban integrato.

## stato

| Fase | Status |
|------|--------|
| Phase 0: MVP Showdown | ✅ |
| Phase 1: Anti-ban + logging + refactoring | ✅ |
| Phase 2: Tactics + game modes multipli | 🔄 in corso |
| Phase 3: ML auto-tuning | ⏳ |

## quick start

```batch
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python debug.py    # calibra HSV per il tuo schermo
python main.py     # avvia
```

Vedi [DEVELOPMENT.md](DEVELOPMENT.md) per setup completo, calibrazione HSV, troubleshooting.

## stack

- Python 3.11 + OpenCV + numpy + mss
- pyautogui + pydirectinput per input
- loguru per logging
- BlueStacks 5 (emulatore Android)

## anti-ban

- Timing jitter ±20% (no pattern fisso)
- Keystroke stagger 5-15ms
- Micro-pause umana 15% probabilità
- Noise direzionale ±8° su movimenti
- Pausa forzata ogni 45 minuti

## contribuire

Repo owned da **Pedro** (Pedronane). Davide collaboratore.
Vedi [.claude/CLAUDE.md](.claude/CLAUDE.md) per divisione compiti e git workflow.
Branch da `dev`, PR verso `dev`.

## disclaimer

Questo progetto è a scopo educativo. L'automazione nei giochi online può violare i termini di servizio.
