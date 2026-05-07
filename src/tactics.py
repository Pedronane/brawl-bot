"""Dizionario politiche tattiche Showdown per fase di gioco.

Le soglie sono calibrate su strategia pro-player documentata:
  - Early: farm cubi, evita combattimento, target 2-4 cubi prima di ingaggiare
  - Mid: picking selettivi, ingaggia solo con vantaggio
  - Late: posizionamento, third-party, ingaggia in ogni caso
"""
from __future__ import annotations

SHOWDOWN_TACTICS: dict[str, dict] = {
    "EARLY": {
        # HP soglie
        "flee_hp": 0.30,                # fuggi se hp < 30%
        "flee_hp_hysteresis": 0.10,     # rientra in FLEEING solo se hp > 40% (30+10)
        "engage_hp": 0.70,              # ingaggia solo se hp > 70%
        # Cubes
        "engage_threshold": 2,          # cubi di vantaggio richiesti per ingaggiare
        # Comportamento
        "farm_priority": True,          # muoviti verso cubi invece di nemici
        "prefer_edges": True,           # stai ai bordi (meno traffico)
        "bush_wait_max": 40,            # frame massimi di attesa in bush
    },
    "MID": {
        "flee_hp": 0.35,
        "flee_hp_hysteresis": 0.10,
        "engage_hp": 0.60,
        "engage_threshold": 1,
        "farm_priority": False,
        "prefer_edges": False,
        "bush_wait_max": 55,
    },
    "LATE": {
        "flee_hp": 0.40,
        "flee_hp_hysteresis": 0.15,     # più isteresi: late game volatile
        "engage_hp": 0.50,              # ingaggia anche con hp bassa
        "engage_threshold": 0,          # ingaggia sempre (deathmatch)
        "farm_priority": False,
        "prefer_edges": False,
        "bush_wait_max": 25,            # meno attesa: late game rapido
    },
    "UNKNOWN": {
        "flee_hp": 0.30,
        "flee_hp_hysteresis": 0.10,
        "engage_hp": 0.70,
        "engage_threshold": 2,
        "farm_priority": True,
        "prefer_edges": True,
        "bush_wait_max": 40,
    },
}

# Tabella decisionale Power Cubes: raccogliere o evitare?
CUBE_RISK: dict[str, dict] = {
    "solo":  {"grab_min_hp": 0.60, "skip_if_enemies_within": 80},
    "vs_1":  {"grab_min_hp": 0.70, "skip_if_enemies_within": 60},
    "vs_2+": {"grab_min_hp": 0.85, "skip_if_enemies_within": 40},
}


def get_tactics(game_phase: str) -> dict:
    """Ritorna dizionario tattiche per la fase corrente."""
    return SHOWDOWN_TACTICS.get(game_phase, SHOWDOWN_TACTICS["UNKNOWN"])


def should_grab_cube(
    hp_ratio: float,
    enemies_nearby: int,
    nearest_enemy_dist: float,
) -> bool:
    """Decisione semplice se vale la pena raccogliere un Power Cube."""
    if enemies_nearby == 0:
        key = "solo"
    elif enemies_nearby == 1:
        key = "vs_1"
    else:
        key = "vs_2+"

    risk = CUBE_RISK[key]
    hp_ok = hp_ratio >= risk["grab_min_hp"]
    safe_dist = nearest_enemy_dist > risk["skip_if_enemies_within"]
    return hp_ok and safe_dist
