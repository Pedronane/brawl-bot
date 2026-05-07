# Development guide — brawl-bot

## requisiti
- Windows 10/11
- Python 3.11+
- BlueStacks 5 (emulatore Android) → vedi sezione installazione
- Brawl Stars installato su BlueStacks

## setup ambiente
```batch
cd Desktop\brawl-bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## installazione BlueStacks
1. Scarica da https://www.bluestacks.com/download.html (BlueStacks 5)
2. Installa → scegli Brawl Stars durante setup O installalo dopo
3. In BlueStacks: Impostazioni → Prestazioni → CPU 4 core, RAM 4GB
4. Game Controls → modalità MOBA → mappa WASD su joystick sinistro

## struttura moduli
| File | Ruolo |
|------|-------|
| `main.py` | Event loop thin — solo cattura + dispatch |
| `src/config.py` | Tutti i parametri (HSV, timing, anti-ban) |
| `src/capture.py` | Screenshot finestra BlueStacks |
| `src/detector.py` | CV2 detection (bush, poison, nemici, AFK) |
| `src/controller.py` | Input WASD o mouse joystick |
| `src/game_state.py` | FrameState immutabile |
| `src/state_machine.py` | Logica stati bot |
| `src/logger.py` | Log console + file con rotazione |
| `src/randomizer.py` | Anti-ban: jitter timing + noise |
| `src/anti_ban.py` | Pausa forzata 45min + session stats |
| `src/utils/geometry.py` | Utility matematica 2D |

## calibrazione HSV (obbligatoria su nuovo PC/risoluzione)

```batch
python debug.py
```

Tasti in debug.py:
- `h` → maschera bush (verde)
- `e` → maschera nemici (rosso HP bar)
- `p` → maschera veleno
- `q` → esci

Se detection sbagliata → modifica `src/config.py`:
```python
BUSH_HSV_LOWER = np.array([H_min, S_min, V_min])
BUSH_HSV_UPPER = np.array([H_max, S_max, V_max])
```
Usa `debug.py` → tasto `h` per visualizzare in real-time.

## avviare il bot

1. Apri BlueStacks → avvia partita Showdown
2. Porta BlueStacks in foreground
3. In terminale:
```batch
python main.py
```
4. Hai 3 secondi per tornare su BlueStacks

Per fermare: `Ctrl+C` nel terminale

## log output
I log sono in `logs/bot_YYYY-MM-DD.log`. Formato JSON-friendly:
```
10:30:15 | INFO    | [MOVING ] dist=142.0
10:30:22 | INFO    | [HIDING ] in cespuglio
10:30:45 | WARNING | Anti-ban: 45min attivi → pausa 5min
```

## git workflow
```
main  ← release stabile
 ↑
 dev  ← integrazione (PR da feature branches)
  ├── feature/[nome]  (Davide o Pedro)
  └── hotfix/[nome]   (urgente da main)
```

### creare feature branch
```bash
git checkout dev
git pull origin dev
git checkout -b feature/nome-feature
# ... sviluppa ...
git push origin feature/nome-feature
# apri PR su GitHub verso dev
```

### commit convention
```
[phase1/logger] implement JSON log rotation
[phase2/tactics] add HideInBushTactic
[fix] poison false positive lower-left corner
[docs] update HSV calibration steps
```

## testing

```batch
pip install pytest pytest-cov
pytest tests/ -v
```

Unit test per detector (mock frame) e geometry utility in `tests/`.

## parametri anti-ban (src/config.py)
| Param | Default | Effetto |
|-------|---------|---------|
| `TIMING_JITTER_PCT` | 0.20 | ±20% varianza loop interval |
| `INPUT_DELAY_CHANCE` | 0.15 | 15% prob. micro-pausa umana |
| `KEYSTROKE_INTERVAL_MIN/MAX` | 5-15ms | stagger tra tasti |
| `SESSION_MAX_MINUTES` | 45 | pausa forzata dopo N min |
| `SESSION_BREAK_MINUTES` | 5 | durata pausa |

## troubleshooting

**BlueStacks non trovato**
→ Controlla `WINDOW_TITLE` in `config.py` (default: "BlueStacks")
→ Verifica finestra visibile non minimizzata

**Bot bloccato (stuck continuo)**
→ `stuck_ratio` alto nei log → aumenta `AVOID_ANGLE` in config.py (default 70°)
→ Ricalibra HSV con debug.py

**Detection bush sbagliata**
→ Ricalibra `BUSH_HSV_LOWER/UPPER` con debug.py tasto 'h'
→ Controlla `BUSH_MIN_AREA` (default 800 px²)

**Poison non rilevato**
→ Ricalibra `POISON_HSV_LOWER/UPPER` con debug.py tasto 'p'
→ Aumenta `POISON_PIXEL_RATIO` (default 0.18)
