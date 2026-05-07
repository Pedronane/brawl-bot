# PEDRO — primo avvio

## 1. clone + setup ambiente
```bash
git clone https://github.com/Pedronane/brawl-bot.git
cd brawl-bot
git checkout dev                   # branch di lavoro
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 2. verifica che tutto funzioni
```bash
python -m pytest tests/ -v
```
Devono passare **22 test**. Se tutti PASSED sei a posto.

## 3. installa BlueStacks (se non ce l'hai)
Scarica: https://www.bluestacks.com/download.html (versione 5)
Setup: Impostazioni → Prestazioni → CPU 4 core, RAM 4GB
Game Controls → MOBA mode → mappa WASD su joystick sinistro
Installa Brawl Stars dentro BlueStacks.

## 4. calibra HSV per il TUO schermo (obbligatorio)
```bash
python debug.py
```
Tasti: `h` = maschera cespugli, `p` = veleno, `e` = nemici, `q` = esci.
Se la maschera non copre bene i cespugli → modifica `src/config.py`:
`BUSH_HSV_LOWER` e `BUSH_HSV_UPPER`

## 5. sync sessione (ogni volta che inizi a lavorare)
```bash
git pull origin dev
node .claude/sync-session.js                    # vedi se Davide sta lavorando su qualcosa
```
Se lo script mostra che Davide sta su file che vuoi toccare tu → contattalo prima.

Per registrare la TUA sessione (sostituisci file con quelli che tocchi):
```bash
node .claude/sync-session.js pedro feature/[nome-branch] src/game_modes/gem_grab.py
git add .claude/.tasks/active.json && git push origin dev
```

## 6. inizia un task
```bash
git checkout dev && git pull origin dev
git checkout -b feature/[numero-issue]-[nome]
# es: feature/3-gem-grab-mode
# lavora sui tuoi file...
git add src/game_modes/gem_grab.py
git commit -m "[phase2/gem-grab] implement gem pit detection"
git push origin feature/3-gem-grab-mode
# apri PR su GitHub verso dev, assegna Davide come reviewer
```

## 7. fine sessione
```bash
node .claude/update-active-session.js pedro [url-pr-opzionale]
git add .claude/.tasks/active.json
git commit -m "[collab] pedro: close session feature/3-gem-grab-mode"
git push origin dev
```

## file tuoi (non toccare quelli di Davide senza avvisare)
```
src/game_modes/     <- TUOI
tests/              <- TUOI
debug.py            <- TUOI

src/tactics.py      <- DAVIDE
src/behavior_engine.py <- DAVIDE
src/state_machine.py   <- DAVIDE
src/logger.py          <- DAVIDE
src/randomizer.py      <- DAVIDE
src/anti_ban.py        <- DAVIDE

src/config.py       <- SHARED (avvisa su COLLAB.md prima)
src/detector.py     <- SHARED (avvisa su COLLAB.md prima)
src/controller.py   <- SHARED (avvisa su COLLAB.md prima)
src/game_state.py   <- SHARED (avvisa su COLLAB.md prima)
main.py             <- SHARED (avvisa su COLLAB.md prima)
```

## dove comunicare con Davide
`.claude/COLLAB.md` — aggiungi messaggio in fondo nella sezione "messaggi", poi:
```bash
git add .claude/COLLAB.md && git commit -m "[collab] pedro: msg davide" && git push origin dev
```
Davide fa `git pull` e vede il messaggio.
