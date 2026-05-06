import numpy as np

WINDOW_TITLE = "BlueStacks"

# ── Controllo ──────────────────────────────────────────────────────────────────
# "keyboard" → WASD (configurare BlueStacks Game Controls → MOBA mode)
# "mouse"    → joystick virtuale via mouse drag (lato sinistro schermo)
CONTROL_MODE = "keyboard"

# Solo per CONTROL_MODE = "mouse": posizione joystick (frazione 0.0-1.0 della finestra)
JOYSTICK_X = 0.20
JOYSTICK_Y = 0.78
JOYSTICK_DRAG_RADIUS = 70  # pixel

# ── Posizione player ───────────────────────────────────────────────────────────
# La camera segue il brawler → il player è sempre al centro schermo
PLAYER_CENTER_X = 0.5
PLAYER_CENTER_Y = 0.5

# ── Colori HSV ────────────────────────────────────────────────────────────────
# Usa debug.py → tasto 'h' per visualizzare la maschera bush e calibrare questi valori

BUSH_HSV_LOWER = np.array([87, 90, 25])
BUSH_HSV_UPPER = np.array([122, 255, 165])

# Veleno/nebbia Showdown (rosa-viola ai bordi mappa)
POISON_HSV_LOWER = np.array([145, 100, 60])
POISON_HSV_UPPER = np.array([175, 255, 210])

# Barre HP nemici (rosso → due range perché HSV è circolare su rosso)
ENEMY_HP_HSV_LOWER_A = np.array([0,  160, 120])
ENEMY_HP_HSV_UPPER_A = np.array([8,  255, 255])
ENEMY_HP_HSV_LOWER_B = np.array([172, 160, 120])
ENEMY_HP_HSV_UPPER_B = np.array([180, 255, 255])

# Avviso AFK (giallo/arancio nell'UI superiore)
AFK_HSV_LOWER = np.array([18, 140, 140])
AFK_HSV_UPPER = np.array([35, 255, 255])

# ── Soglie ─────────────────────────────────────────────────────────────────────
BUSH_MIN_AREA = 800          # px² minima area contorno → filtra rumore
BUSH_MORPH_KERNEL = 7        # kernel morfologia → elimina griglia tiles

# Zone UI da escludere dalla detection (frazione 0-1 della finestra)
# Joystick basso-sx e bottoni attacco basso-dx
UI_EXCLUDE = [
    (0.0, 0.68, 0.28, 1.0),   # (x1,y1,x2,y2) joystick area basso-sx
    (0.72, 0.60, 1.0,  1.0),  # bottoni attacco basso-dx
    (0.88, 0.0,  1.0,  0.85), # pannello UI lato destro
    (0.0,  0.0,  1.0,  0.06), # barra superiore BlueStacks
]
BUSH_REACH_DIST = 8          # px dal bordo contorno → quasi dentro
POISON_EDGE_FRACTION = 0.18  # margine bordo da controllare per veleno
POISON_PIXEL_RATIO = 0.18    # almeno 18% dei pixel nel margine devono essere veleno
AFK_ROI_PIXEL_SUM = 2500     # somma pixel gialli in ROI AFK per trigger

WIGGLE_INTERVAL = 35         # frame tra ogni wiggle anti-AFK (~2.8s)
WIGGLE_DURATION = 0.09       # secondi per ogni direzione nel wiggle

LOOP_INTERVAL = 0.08         # secondi tra iterazioni (~12 fps)
