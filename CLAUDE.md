# brawl-bot

Python bot Brawl Stars su BlueStacks (Windows).
Collaboratori: Pedro (owner) + Davide.

**Workflow e regole complete → `.claude/CLAUDE.md`**
Roadmap → `ROADMAP.md`
Setup → `DEVELOPMENT.md`

## stack
Python 3.11 · OpenCV · numpy · mss · pyautogui · pydirectinput · loguru

## comandi
- `python debug.py` — calibra HSV
- `python main.py` — avvia bot
- `pip install -r requirements.txt` — installa dipendenze

## struttura
- `src/` — moduli bot (capture, detector, controller, state_machine, logger, randomizer, anti_ban)
- `config/` — yaml configurazione (Fase 2)
- `logs/` — output sessioni (gitignore)
- `tests/` — unit test
- `.claude/` — context Claude Code + sistema collab

## sessione collab (obbligatorio)
```bash
git pull origin dev
node .claude/sync-session.js                                          # check stato
node .claude/sync-session.js [davide|pedro] [branch] [file1,file2]   # registra sessione
git add .claude/.tasks/active.json && git push origin dev
```
Fine sessione:
```bash
node .claude/update-active-session.js [davide|pedro]
git add .claude/.tasks/active.json && git push origin dev
```
