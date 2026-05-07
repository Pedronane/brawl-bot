# Prompt da dare al Claude Code di Pedro — copia-incolla come PRIMO messaggio

---

Sono Pedro, collaboratore del progetto brawl-bot con Davide (Pedronane/brawl-bot).
Ho appena clonato il repo. Esegui questo setup nella cartella brawl-bot.

## Step 1 — leggi il contesto
Leggi in ordine questi file:
1. `CLAUDE.md` — overview progetto
2. `.claude/CLAUDE.md` — regole workflow, file ownership, come lavorare
3. `.claude/PEDRO_START.md` — setup specifico per me
4. `.claude/COLLAB.md` — stato task board, messaggi da Davide
5. `ROADMAP.md` — fasi 1/2/3

## Step 2 — setup ambiente
```bash
git checkout dev
git pull origin dev
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3 — verifica setup
```bash
python -m pytest tests/ -v -m "not hardware"
```
Devono passare 22 test. Se tutti PASSED procedi.

## Step 4 — verifica sync con Davide
```bash
node .claude/sync-session.js
```
Mostra chi sta lavorando su cosa. Leggi output prima di iniziare qualsiasi task.

## Step 5 — calibra HSV (obbligatorio prima di lavorare su detection)
Apri BlueStacks → avvia Brawl Stars → entra in una partita Showdown → poi:
```bash
python debug.py
```
Tasti: `h` = cespugli (deve coprire il verde), `p` = veleno, `e` = nemici, `q` = esci.
Se la maschera non è precisa → modifica `src/config.py` BUSH_HSV_LOWER/UPPER.

## Step 6 — registra sessione e inizia task
```bash
# Controlla COLLAB.md per task assegnati a te
# Prendi un task dalla ROADMAP che non è "in corso"
git checkout dev && git pull origin dev
git checkout -b feature/[numero-task]-[nome]

# Registra la sessione (sostituisci file con quelli che tocchi)
node .claude/sync-session.js pedro feature/[nome] src/game_modes/showdown.py
git add .claude/.tasks/active.json && git push origin dev
```

## Regole fondamentali (non derogabili)
- **MAI** lavorare su `dev` o `main` direttamente — sempre branch `feature/`
- **MAI** toccare file owned da Davide senza prima scrivergli su COLLAB.md
- File tuoi: `src/game_modes/`, `tests/`, `debug.py`
- File Davide: `src/tactics.py`, `src/state_machine.py`, `src/logger.py`, `src/randomizer.py`, `src/anti_ban.py`, `src/behavior_engine.py`
- File shared (avvisa prima): `src/config.py`, `src/detector.py`, `src/controller.py`, `src/game_state.py`, `main.py`

## Fine sessione (sempre)
```bash
node .claude/update-active-session.js pedro [url-pr-se-aperta]
git add .claude/.tasks/active.json
git commit -m "[collab] pedro: close session [branch]"
git push origin dev
```

## Come fermare il bot se va fuori controllo
- **Ctrl+C** nel terminale
- Oppure crea il file `kill.flag` nella cartella brawl-bot (il bot si ferma entro 1 secondo)
- In caso estremo: Task Manager → termina `python.exe`

## Come comunicare con Davide
Aggiungi messaggio in `.claude/COLLAB.md` sezione "messaggi", poi:
```bash
git add .claude/COLLAB.md && git commit -m "[collab] pedro: [oggetto]" && git push origin dev
```
Davide fa `git pull` e vede il messaggio.

---

Dopo aver letto tutto, dimmi:
1. Cosa trovi nel COLLAB.md come messaggi da Davide
2. Quale task è disponibile per me in ROADMAP.md
3. Se i 22 test passano tutti

Poi proponi su quale task iniziare.
Comunicazione: italiano.

---
