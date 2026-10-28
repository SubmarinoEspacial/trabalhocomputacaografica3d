"""Parâmetros da cena e da abdução. Ajuste aqui, sem mexer na lógica."""
import math

# Submarino
SUB_START = (-8.0, 1.0, 0.0)
SUB_SPEED = 1.5
SUB_SPEED_FLEE = 3.0
PROP_SPEED = 6.0            # rad/s

# Disco voador
DISC_START = (2.0, 5.0, -3.0)
DISC_SPEED = 3.0
DISC_HOVER_AMP = 0.15
DISC_HOVER_FREQ = 2.0
DISC_HEIGHT_OVER_SUB = 3.0
RING_SPEED = 2.0            # rad/s

# Interação
DETECT_RADIUS = 5.0
ARRIVE_EPS = 0.3
ORBIT_RADIUS = 2.5
ORBIT_OMEGA = math.pi / 2   # rad/s (uma volta em 4 s)
FLEE_TIME = 1.5
BEAM_TIME = 1.0
ABDUCT_TIME = 4.0
ABDUCT_RISE = 2.5
ABDUCT_SPIN = 2.0           # rad/s
ABDUCT_MIN_SCALE = 0.4
FINAL_WAIT = 1.5
