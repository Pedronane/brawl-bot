# brawl-bot — context Claude Code

## what it is
Python bot Brawl Stars su BlueStacks (Windows). Screen capture + CV2 → input WASD/mouse.
Anti-ban: timing randomizzato, pausa forzata 45min, rumore direzionale.

## team
- **Pedro** (repo owner, Claude pro): game mode implementations, testing, HSV calibration
- **Davide** (collaboratore, Claude max): arch, refactoring, feature avanzate, ML, review PR

---

## WORKFLOW OBBLIGATORIO — LEGGI PRIMA DI TOCCARE QUALSIASI FILE

### INIZIO SESSIONE — 3 comandi, sempre, nessuna eccezione
```bash
git pull origin dev
node .claude/sync-session.js                          # mostra chi sta lavorando
node .claude/sync-session.js [te] [branch] [file1,file2,...]  # registra la tua sessione
git add .claude/.tasks/active.json && git push origin dev     # rendi visibile agli altri
```
Esempio Davide:
```bash
node .claude/sync-session.js davide feature/7-tactics src/tactics.py,src/behavior_engine.py
```
Se lo script mostra ⚠️ CONFLITTO → **non iniziare** finché non risolto.

### FINE SESSIONE — sempre
```bash
node .claude/update-active-session.js [te] [pr_url?]
git add .claude/.tasks/active.json .claude/COLLAB.md
git commit -m "[collab] [te]: close session [branch]"
git push origin dev
```

### regola 1 — inizio sessione sempre
```bash
git pull origin dev          # sync stato remoto
```
Poi controlla GitHub Issues: https://github.com/Pedronane/brawl-bot/issues
Prendi solo issue assegnata a te. Se non assegnata, assegnatela PRIMA di iniziare.

### regola 2 — ogni task = branch separato SEMPRE
```bash
git checkout dev
git pull origin dev
git checkout -b feature/[numero-issue]-[nome-breve]
# es: feature/7-tactics-engine
```
**MAI lavorare direttamente su dev o main.**

### regola 3 — file ownership (non toccare file dell'altro senza issue)
| File / cartella | Owner | |
|-----------------|-------|-|
| `src/tactics.py` | Davide | |
| `src/behavior_engine.py` | Davide | |
| `src/state_machine.py` | Davide | |
| `src/logger.py` | Davide | |
| `src/randomizer.py` | Davide | |
| `src/anti_ban.py` | Davide | |
| `src/ml/` | Davide | |
| `src/game_modes/` | Pedro | |
| `tests/` | Pedro | |
| `debug.py` | Pedro | |
| `src/capture.py` | shared — crea branch, avvisa su issue |
| `src/detector.py` | shared — crea branch, avvisa su issue |
| `src/controller.py` | shared — crea branch, avvisa su issue |
| `src/config.py` | shared — crea branch, avvisa su issue |
| `src/game_state.py` | shared — crea branch, avvisa su issue |
| `main.py` | shared — crea branch, avvisa su issue |

Per file "shared": commenta sull'issue GitHub che stai modificando quel file. L'altro vede la notifica e aspetta.

### regola 4 — fine task → PR, mai merge diretto
```bash
git push origin feature/[nome]
# apri PR su GitHub verso dev
# assegna l'altro come reviewer
```
PR deve passare review dell'altro prima del merge su dev.

### regola 5 — conflitti su file shared
Se devi modificare un file owned dall'altro o shared:
1. Apri Issue GitHub con titolo: `[SHARED] modifica src/config.py per [motivo]`
2. L'altro risponde OK o propone alternativa
3. Solo dopo → lavori sul branch

---

## phase status
- [x] Phase 0: MVP Showdown base
- [x] Phase 1: Anti-ban + logging + refactoring (struttura src/)
- [ ] Phase 2: Tactics engine + game modes multipli
- [ ] Phase 3: ML (HSV optimizer, strategy learner)

## struttura
```
main.py             thin event loop
src/
  config.py         parametri HSV, anti-ban, timing
  capture.py        screenshot BlueStacks (mss + win32gui)
  detector.py       CV2: cespugli, nemici, veleno, AFK
  controller.py     input WASD / mouse joystick + randomizer
  game_state.py     dataclass immutabile FrameState
  state_machine.py  logica stati (HIDING/MOVING/FLEEING/WAITING)
  logger.py         loguru: console + file rotation in logs/
  randomizer.py     jitter timing, noise direction, human pause
  anti_ban.py       pausa forzata 45min, session stats
  utils/geometry.py normalize/rotate/distance
logs/               output bot (gitignore)
tests/              unit test
config/             yaml Fase 2
data/               ML weights Fase 3
```

## vincoli critici
1. screen-only: no memory read, no packet injection, no API ufficiale
2. anti-ban: mai pattern fissi, jitter ±20% timing, noise su direzioni
3. Windows + BlueStacks: mss, win32gui, pyautogui/pydirectinput
4. CV2/HSV: no pre-trained model, calibrare con debug.py

## calibrazione HSV
```
python debug.py   # tasto 'h' → maschera bush, 'e' → nemici, 'p' → veleno
```
Valori in src/config.py: BUSH_HSV_LOWER/UPPER, POISON_HSV_LOWER/UPPER

## setup locale
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python debug.py    # calibra
python main.py     # avvia bot
```

## commit format
```
[phase2/tactics] add TacticSelector priority logic
[phase2/gem-grab] implement gem pit detection
[fix] poison false positive lower-left corner
[shared/config] add THREAT_THRESHOLD param
```
