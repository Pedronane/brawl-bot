# collab — stato condiviso tra Claude Code di Davide e Pedro

> **REGOLA:** Ogni sessione di lavoro:
> 1. `git pull origin dev` — leggi aggiornamenti
> 2. Leggi questo file PRIMA di iniziare
> 3. Alla fine: aggiorna sezione "ultimo update" + push

---

## stato attuale progetto

**branch attivo:** dev
**fase:** 1 COMPLETATA → 2 in corso
**ultimo sync:** 2026-05-07

---

## task board

### in corso
| task | chi | branch | note |
|------|-----|--------|------|
| — | — | — | — |

### da fare (Davide)
| task | priorità | file target |
|------|----------|-------------|
| src/tactics.py — TacticSelector + 4 tactic classes | ALTA | src/tactics.py |
| src/game_modes/base.py — interfaccia GameMode | ALTA | src/game_modes/base.py |
| enemy threat level 0.0→1.0 in detector.py | MEDIA | src/detector.py |
| behavior_engine.py | MEDIA | src/behavior_engine.py |

### da fare (Pedro)
| task | priorità | file target |
|------|----------|-------------|
| src/game_modes/showdown.py — migra logica attuale | ALTA | src/game_modes/ |
| src/game_modes/gem_grab.py | MEDIA | src/game_modes/ |
| HSV calibration brawl ball / gem grab | BASSA | config/hsv_profiles.yaml |
| test su PC con BlueStacks | SEMPRE | — |

### completati
| task | chi | data |
|------|-----|------|
| struttura src/ + moduli Fase 1 | Davide | 2026-05-07 |
| logger, randomizer, anti_ban, game_state | Davide | 2026-05-07 |
| state_machine.py estratto + main.py thin | Davide | 2026-05-07 |
| ROADMAP.md, DEVELOPMENT.md, docs | Davide | 2026-05-07 |

---

## messaggi

> **[Davide → Pedro] 2026-05-07**
> Setup Fase 1 completo e testato. Leggi PEDRO_CLAUDE_PROMPT.md per avviarti da zero.
>
> Cosa c'è nel repo:
> - src/ con tutti i moduli (capture, detector, controller, state_machine, logger, randomizer, anti_ban, game_state)
> - 22 test pytest che passano tutti: `python -m pytest tests/ -v -m "not hardware"`
> - Sistema anti-ban (timing jitter, kill.flag per fermare il bot, window focus check)
> - Sistema collab: sync-session.js per vedere chi lavora su cosa
> - CI GitHub Actions configurata (.github/workflows/ci.yml)
> - Ruff linting: zero errori
>
> Il tuo primo task (Fase 2):
> **Crea `src/game_modes/showdown.py`** — migra la logica Showdown da state_machine.py in un modulo separato.
> File che tocchi: `src/game_modes/showdown.py` (nuovo), puoi guardare `src/state_machine.py` per capire la logica attuale.
> NON modificare state_machine.py — contattami prima se devi.
>
> Io intanto faccio `src/tactics.py` e `src/game_modes/base.py` (interfaccia).
> Quando finisci showdown.py apri PR verso dev e assegnami come reviewer.
> Scrivi msg qui quando hai pushato così mi allineo.

---

## blockers / domande aperte

| problema | chi aspetta | data |
|----------|-------------|------|
| — | — | — |

---

## come aggiornare questo file

Alla fine di ogni sessione:
```
# aggiungi riga in "completati"
# togli da "in corso"  
# aggiungi msg nella sezione messaggi con [Nome → Nome] data
git add .claude/COLLAB.md
git commit -m "[collab] update task board + msg"
git push origin dev
```
