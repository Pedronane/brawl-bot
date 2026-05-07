# roadmap brawl-bot

## fase 0 — MVP ✅
state machine Showdown base, bush detection HSV, poison flee, wall avoidance, AFK wiggle

## fase 1 — fondamenta ✅
- struttura src/ (capture, detector, controller, config, game_state, state_machine)
- logger.py: loguru console + file rotation in logs/
- randomizer.py: jitter ±20% timing, noise ±8° direzione, keystroke stagger
- anti_ban.py: pausa forzata 45min, session stats
- utils/geometry.py: normalize/rotate/distance
- main.py thin wrapper
- docs: CLAUDE.md, DEVELOPMENT.md, README.md

## fase 2 — intelligenza 🔄
**arco: 3-4 settimane**

### tactics engine (Davide)
- `src/tactics.py`: classi tactic base + TacticSelector priority-based
  - HideInBushTactic, FleePoison, AvoidEnemyTactic, PatrolTactic
- enemy threat level 0.0→1.0 (distanza + num nemici + poison proximity)
- threat integrato in state_machine.py: nuovo stato ENGAGING

### game modes (Pedro implementa, Davide design base)
- `src/game_modes/base.py`: interfaccia GameMode
- `src/game_modes/showdown.py`: migra logica attuale
- `src/game_modes/gem_grab.py`: gem pit detection + movimento
- `src/game_modes/brawl_ball.py`: positioning dinamico
- `src/game_modes/heist.py`, `bounty.py`
- auto-detect game mode da UI: `detector.detect_game_mode(frame)`

### config yaml (fase 2)
- `config/tactics.yaml`: soglie tattica per game mode
- `config/game_modes.yaml`: obiettivi per mode
- `config/hsv_profiles.yaml`: HSV per mode diversi

### behavior engine (Davide)
- `src/behavior_engine.py`: adatta parametri runtime
  - stuck_ratio alto → aumenta AVOID_ANGLE
  - enemy freq alta → riduce LOOP_INTERVAL
  - poison spesso → aumenta POISON_EDGE_FRACTION

## fase 3 — ML ⏳
**arco: 4-6 settimane dopo fase 2**

### HSV auto-calibration
- `src/ml/hsv_optimizer.py`: algoritmo genetico leggero
  - population 10 HSV sets, fitness = detection precision
  - mutation ±5% per bound, 5-10 generazioni
  - save best → `data/hsv_best.json`

### strategy learner
- `src/ml/strategy_learner.py`: replay buffer tactic → survival time
  - aggiorna weights tattiche settimanalmente
  - save → `data/strategy_weights.json`

### anomaly detector
- `src/ml/anomaly_detector.py`: baseline metrics + alert σ>2
  - auto-reset HSV se falso positivo ripetuto

## struttura target finale
```
brawl-bot/
├── src/
│   ├── [fase 1 files] ✅
│   ├── tactics.py              [F2]
│   ├── behavior_engine.py      [F2]
│   ├── game_modes/             [F2]
│   │   ├── base.py
│   │   ├── showdown.py
│   │   ├── gem_grab.py
│   │   ├── brawl_ball.py
│   │   ├── heist.py
│   │   └── bounty.py
│   └── ml/                     [F3]
│       ├── hsv_optimizer.py
│       ├── strategy_learner.py
│       └── anomaly_detector.py
├── config/                     [F2]
│   ├── tactics.yaml
│   ├── game_modes.yaml
│   └── hsv_profiles.yaml
├── data/                       [F3]
│   ├── hsv_best.json
│   └── strategy_weights.json
├── tests/
└── logs/
```

## divisione compiti

| Task | Chi | Fase |
|------|-----|------|
| Arch + refactoring + review | Davide | tutte |
| tactics.py + behavior_engine.py | Davide | F2 |
| ML pipeline | Davide | F3 |
| game_modes implementations | Pedro | F2 |
| HSV calibration per mode | Pedro | F2 |
| Testing + bug reports | Pedro | F1-F3 |
| game_modes/base.py design | Davide | F2 |

## anti-ban notes
- no pattern fissi: randomizer.py attivo su ogni input
- no 24/7: anti_ban.py pausa 5min ogni 45min
- variazione: noisy_direction ±8° su ogni move
- invisibile: screen-only, no memory/packet
