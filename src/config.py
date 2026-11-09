"""Parâmetros da cena e da abdução. Ajuste aqui, sem mexer na lógica."""
import math
import sys


def _qualidade_da_linha_de_comando():
    argumentos = sys.argv[1:]
    for indice, argumento in enumerate(argumentos):
        if argumento == "--quality" and indice + 1 < len(argumentos):
            return argumentos[indice + 1].lower()
        if argumento == "--qualidade" and indice + 1 < len(argumentos):
            return argumentos[indice + 1].lower()
        if argumento.startswith("--quality="):
            return argumento.split("=", 1)[1].lower()
        if argumento.startswith("--qualidade="):
            return argumento.split("=", 1)[1].lower()
    return "media"


_PERFIS_QUALIDADE = {
    # baixa: menos sombras, água e luzes; indicada para máquinas fracas.
    "baixa": {
        "SHADOW_RESOLUTION": 1024,
        "SHADOW_PCF_SAMPLES": 1,
        "WATER_GRID_RESOLUTION": 80,
        "WATER_WAVE_COUNT": 3,
        "MAX_POINT_LIGHTS": 2,
        "POST_BLOOM_ENABLED": False,
        "ROUND_SEGMENTS": 8,
        "ROUND_RINGS": 6,
        "SMALL_SEGMENTS": 6,
        "SMALL_RINGS": 4,
        "DISC_RING_LIGHTS": 8,
        "DETALHES_COMPLETOS": False,
    },
    # media: padrão equilibrado entre leitura visual e desempenho.
    "media": {
        "SHADOW_RESOLUTION": 1024,
        "SHADOW_PCF_SAMPLES": 4,
        "WATER_GRID_RESOLUTION": 80,
        "WATER_WAVE_COUNT": 5,
        "MAX_POINT_LIGHTS": 2,
        "POST_BLOOM_ENABLED": True,
        "ROUND_SEGMENTS": 12,
        "ROUND_RINGS": 8,
        "SMALL_SEGMENTS": 8,
        "SMALL_RINGS": 5,
        "DISC_RING_LIGHTS": 8,
        "DETALHES_COMPLETOS": False,
    },
    # alta: qualidade visual próxima à versão anterior.
    "alta": {
        "SHADOW_RESOLUTION": 2048,
        "SHADOW_PCF_SAMPLES": 9,
        "WATER_GRID_RESOLUTION": 200,
        "WATER_WAVE_COUNT": 5,
        "MAX_POINT_LIGHTS": 4,
        "POST_BLOOM_ENABLED": True,
        "ROUND_SEGMENTS": 32,
        "ROUND_RINGS": 16,
        "SMALL_SEGMENTS": 12,
        "SMALL_RINGS": 6,
        "DISC_RING_LIGHTS": 16,
        "DETALHES_COMPLETOS": True,
    },
}

QUALITY = _qualidade_da_linha_de_comando()
if QUALITY not in _PERFIS_QUALIDADE:
    raise SystemExit("--quality/--qualidade deve ser: baixa, media ou alta")


def aplicar_perfil_qualidade(nome):
    """Troca os parâmetros de renderização para um perfil conhecido."""
    global QUALITY
    nome = nome.lower().strip()
    if nome not in _PERFIS_QUALIDADE:
        raise ValueError("perfil de qualidade desconhecido: " + nome)
    QUALITY = nome
    for chave, valor in _PERFIS_QUALIDADE[nome].items():
        globals()[chave] = valor


aplicar_perfil_qualidade(QUALITY)

# Atmosfera noturna
SKY_COLOR = (0.002, 0.006, 0.018, 1.0)   # clear color; o domo cobre a tela
SKY_ZENITH_COLOR = (0.002, 0.006, 0.020)
SKY_HORIZON_COLOR = (0.018, 0.045, 0.085)
SKY_GROUND_COLOR = (0.002, 0.004, 0.010)
STAR_INTENSITY = 1.0
FOG_COLOR = SKY_HORIZON_COLOR
FOG_START = 28.0
FOG_END = 125.0
FOG_DENSITY = 0.018
EXPOSURE = 1.45
GAMMA = 1.25
POST_BLOOM_STRENGTH = 0.62
POST_BLOOM_THRESHOLD = 0.66
POST_VIGNETTE_STRENGTH = 0.55
POST_COOL_TINT = (0.72, 0.88, 1.25)

# Janela e quadros
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 540
FRAME_LIMIT = 60

# Mar aberto
WATER_LEVEL = 1.5
WATER_WIDTH = 160.0
WATER_DEPTH = 130.0
SEA_FLOOR_DEPTH = 18.0
WATER_COLOR = (0.012, 0.075, 0.13)
WATER_ALPHA = 0.58
WATER_WAVES = (
	(1.0, 0.0, 0.18, 0.32, 0.85),
	(0.6, 0.8, 0.11, 0.55, 1.2),
	(-0.8, 0.6, 0.07, 0.9, 1.55),
)
# Ondas menores somadas às três principais; CPU e GPU usam a mesma lista.
WATER_DETAIL_WAVES = (
	(0.28, -0.96, 0.045, 2.4, 2.2),
	(-0.8, -0.6, 0.028, 3.6, 2.9),
)
WATER_SPECULAR_STRENGTH = 1.35
WATER_FOAM_SCALE = 0.24
WATER_FOAM_STRENGTH = 0.48

# Espuma de contato e esteira do submarino
FOAM_COLOR = (0.72, 0.84, 0.92)
FOAM_CONTACT_ALPHA = 0.62
FOAM_WAKE_ALPHA = 0.34

# Lua e iluminação noturna
# A direção é a dos raios; a lua visível fica no sentido oposto, à frente da câmera.
# A elevação baixa mantém a lua no enquadramento inicial e alonga as sombras.
MOON_DIRECTION = (0.54, -0.08, 0.84)
MOON_COLOR = (0.62, 0.74, 1.0)
MOON_STRENGTH = 1.15
MOON_ANGULAR_RADIUS = 2.6    # graus; diâmetro aparente de 5,2 graus
AMBIENT_COLOR = (0.075, 0.11, 0.21)
AMBIENT_STRENGTH = 0.9

# Sombras lunares
SHADOW_ORTHO_SIZE = 26.0
SHADOW_BIAS = 0.0010
SHADOW_FOCUS_HEIGHT = 1.4
SHADOW_FOLLOW_SPEED = 5.0    # suaviza o deslocamento do centro da sombra

# Submarino
SUB_DEPTH = 3.0
SUB_SURFACE_OFFSET = -0.65
SUB_TOWER_TOP = 1.85
SUB_START = (-11.0, WATER_LEVEL - SUB_DEPTH, 0.0)
SUB_SPEED = 1.3
SUB_SPEED_FLEE = 2.2
PROP_SPEED = 6.0            # rad/s
SUBMERGED_TIME = 2.5
EMERGE_TIME = 3.2
EMERGE_PITCH = 12.0         # graus, nariz inclinado ao romper a água
SURFACE_ROLL_FACTOR = 0.65
DETECTION_APPROACH_RADIUS = 10.0
SUB_GLOW_COLOR = (0.12, 0.72, 1.0)
GLOW_RISE_TIME = 1.5
GLOW_PULSE_AMPLITUDE = 0.16
GLOW_PULSE_FREQUENCY = 3.0
GLOW_FADE_SPEED = 1.0

# Disco voador
DISC_SCALE = 2.7
DISC_START = (7.0, 8.0, -6.0)
DISC_SPEED = 5.5
DISC_HOVER_AMP = 0.15
DISC_HOVER_FREQ = 2.0
DISC_HEIGHT_OVER_SUB = 7.5
DISC_HOVER_RADIUS = 0.2
RING_SPEED = 2.0            # rad/s
DISC_LIGHT_COLORS = (
	(1.0, 0.10, 0.04),
	(0.06, 1.0, 0.28),
	(0.10, 0.46, 1.0),
	(1.0, 0.68, 0.08),
	(0.82, 0.92, 1.0),
)
BEAM_COLOR = (0.30, 0.72, 1.0)
BEAM_CORE_COLOR = (0.85, 0.97, 1.0)
BEAM_OUTER_ALPHA = 0.62
BEAM_CORE_ALPHA = 0.88

# Luzes pontuais dinâmicas (máximo efetivo vem do perfil de qualidade)
SUB_PORTHOLE_LIGHT_COLOR = (1.0, 0.58, 0.20)
SUB_PORTHOLE_LIGHT_STRENGTH = 1.45
SUB_PORTHOLE_LIGHT_RANGE = 6.5
SUB_SEARCHLIGHT_COLOR = (0.40, 0.78, 1.0)
SUB_SEARCHLIGHT_STRENGTH = 1.70
SUB_SEARCHLIGHT_RANGE = 10.0
UFO_GLOW_LIGHT_COLOR = (0.20, 0.58, 1.0)
UFO_GLOW_LIGHT_STRENGTH = 1.15
UFO_GLOW_LIGHT_RANGE = 9.0
UFO_BEAM_LIGHT_COLOR = (0.35, 0.80, 1.0)
UFO_BEAM_LIGHT_STRENGTH = 3.20
UFO_BEAM_LIGHT_RANGE = 15.0

# Anel de impacto do feixe na superfície
IMPACT_RING_COLOR = (0.33, 0.80, 1.0)
IMPACT_RING_SIZE = 6.0
IMPACT_RING_ALPHA = 0.90

# Interação
DETECT_RADIUS = 20.0
DETECT_APPROACH_RADIUS = 10.0
ARRIVE_EPS = 0.45
ORBIT_RADIUS = 4.2
ORBIT_OMEGA = math.pi / 2   # rad/s (uma volta em 4 s)
BEAM_TIME = 1.5
ABDUCT_TIME = 6.0
ABDUCT_RISE = 6.4
ABDUCT_SPIN = math.pi / 6   # rad/s: meia volta ao longo dos 6 s de subida
ABDUCT_MIN_SCALE = 0.05
FINAL_WAIT = 1.2
