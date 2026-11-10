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
        "WATER_WAVE_COUNT": 2,
        "MAX_POINT_LIGHTS": 2,
        "POST_BLOOM_ENABLED": False,
        "RENDER_SCALE": 1.0,
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
        "WATER_WAVE_COUNT": 3,
        "MAX_POINT_LIGHTS": 2,
        "POST_BLOOM_ENABLED": False,
        "RENDER_SCALE": 1.0,
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
        "RENDER_SCALE": 1.0,
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
EXPOSURE = 1.20
GAMMA = 1.20
POST_BLOOM_STRENGTH = 0.72
POST_BLOOM_THRESHOLD = 0.60
POST_VIGNETTE_STRENGTH = 0.55
POST_COOL_TINT = (0.72, 0.88, 1.25)

# Janela e quadros; o tamanho inicial preserva o desempenho da versão anterior.
WINDOW_SIZE = (960, 540)
MIN_WINDOW_SIZE = (640, 360)
# Escala do render interno: 1.0 = nativa; a qualidade adaptativa usa 0.85/0.70/0.50.
# Desempenho e qualidade adaptativa.
TARGET_FPS = 60                 # T alterna 60/120; V libera o limitador.
FRAME_LIMIT = TARGET_FPS
DEBUG_GL = False                # True religa as checagens de erro do PyOpenGL.
GC_INTERVAL = 10.0              # coleta manual do gc a cada N segundos.
ADAPTIVE_QUALITY = True
ADAPTIVE_DOWN_FPS = 0.90        # abaixo de 90% do alvo por 2 s reduz um nível
ADAPTIVE_UP_FPS = 1.10          # acima de 110% do alvo por 5 s sobe um nível
ADAPTIVE_DOWN_TIME = 2.0
ADAPTIVE_UP_TIME = 5.0

# HUD compacto (Parte A).
HUD_SCALE = 1.0                 # multiplica a fonte; 1.0 ~ 1,5% da altura

# Câmera inicial e controles (rig de voo: yaw no pai, pitch no filho).
CAMERA_START_POSITION = (0.0, 13.0, 34.0)
CAMERA_START_YAW = 0.0
CAMERA_START_PITCH = -17.0
PITCH_LIMIT = 85.0
CAMERA_MOVE_SPEED = 8.0          # unidades por segundo
CAMERA_TURN_SPEED = 90.0         # graus por segundo
CAMERA_RUN_MULTIPLIER = 3.0      # SHIFT multiplica a velocidade horizontal

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

# Luzes emissivas centralizadas: cor branca única e intensidades à parte.
LIGHT_COLOR = [1.0, 1.0, 1.0]    # branco; glUniform aceita lista e LambertMaterial converte em tupla
LIGHT_INTENSITY = 3.0            # multiplica as emissões (emissiveStrength); >1 estoura de forma suave
BEAM_INTENSITY = 2.4             # multiplica a cor do feixe e do anel de impacto
HALO_INTENSITY = 1.5             # emissiveStrength do casco do submarino durante a abdução
POINTLIGHT_INTENSITY = 1.7       # multiplica a força das PointLights dinâmicas
# True: bombordo vermelha e boreste verde (realismo). False: tudo branco.
NAV_LIGHTS_COLORED = True
NAV_BOMBORDO_COLOR = (1.0, 0.06, 0.025)
NAV_BORESTE_COLOR = (0.04, 1.0, 0.30)

# Cores dos veículos (pintura): centralizadas para ajuste fino.
SUB_COLOR_CASCO = (0.35, 0.42, 0.52)        # cinza-azulado médio
SUB_COLOR_CASCO_TEX = (0.72, 0.79, 0.89)    # tom da textura pintada (convés e chapas)
SUB_COLOR_TORRE = (0.30, 0.37, 0.47)        # torre um tom abaixo do casco
SUB_COLOR_FAIXA = (0.20, 0.26, 0.34)        # linha d'água e faixas de emenda
SUB_COLOR_METAL = (0.50, 0.55, 0.61)        # ferragens e corrimãos
SUB_COLOR_LATAO = (0.52, 0.42, 0.19)        # latão dos aros e torretas
SUB_COLOR_BORRACHA = (0.09, 0.11, 0.13)     # linha de flutuação/separadores
SUB_COLOR_HELICE = (0.52, 0.36, 0.13)       # hélice bronzeada

DISC_COLOR_CASCO = (0.65, 0.68, 0.75)       # casco prateado claro
DISC_COLOR_CASCO_ESCURO = (0.40, 0.44, 0.51)  # barriga e camadas inferiores
DISC_COLOR_PAINEL = (0.55, 0.58, 0.66)      # painéis um pouco mais escuros que o casco
DISC_COLOR_METAL = (0.72, 0.74, 0.78)       # aro metálico e antena
DISC_COLOR_LATAO = (0.55, 0.45, 0.20)       # aro da base e emissor
DISC_COLOR_DOMO = (0.30, 0.40, 0.58)        # cúpula de vidro azulada translúcida
DISC_COLOR_COCKPIT = (0.10, 0.28, 0.38)     # cabine interna sob o domo

# Modo apresentação (só veículos): realça a forma sem clarear o cenário.
# L liga/desliga em tempo de execução; nenhum objeto de luz/passe novo é criado.
PRESENT_MODE = 1
PRESENT_AMBIENT_TOP = (0.30, 0.38, 0.55)    # céu claro no zênite
PRESENT_AMBIENT_BOTTOM = (0.08, 0.12, 0.20)  # mar escuro no nadir
PRESENT_AMBIENT = 0.9                       # intensidade do ambiente hemisférico
PRESENT_FILL_SOURCE = (0.35, 0.42, 1.0)     # direção PARA a fonte (oposto à lua, lado da câmera)
PRESENT_FILL_COLOR = (0.42, 0.50, 0.62)     # azul frio e fraco
PRESENT_FILL = 0.55                         # intensidade do preenchimento (sem sombra)
PRESENT_RIM_COLOR = (0.75, 0.82, 0.95)      # azul-prateado do contorno
PRESENT_RIM = 0.9                           # intensidade do rim/Fresnel
PRESENT_RIM_POWER = 3.0                     # potência do Fresnel (maior = mais fino)
PRESENT_FOG_FACTOR = 0.3                    # neblina 70% mais fraca nos veículos
PRESENT_VEHICLE_EXPOSURE = 1.15             # exposição extra só dos veículos


# HUD (interface sobreposta): controles listados no canto e na documentação.
# Mantemos uma única fonte de verdade — README e HUD leem desta lista.
CONTROLS = [
    ("W/A/S/D", "Câmera"),
    ("Q/E", "Altura"),
    ("Setas", "Rotação"),
    ("SHIFT", "Corrida"),
    ("ESPAÇO", "Pausa"),
    ("R", "Reiniciar"),
    ("F1", "HUD"),
    ("F2/F4/F5", "Perfis"),
    ("F3", "Tempos"),
    ("F11/Alt+Enter", "Tela"),
    ("ESC", "Sair/sobre"),
    ("H", "Controles"),
    ("I", "Sobre"),
    ("L", "Apresentação"),
    ("V", "Limite FPS"),
    ("T", "Alvo 60/120"),
    ("G", "Adaptativo"),
]

STUDENT_NAMES = [
    "Integrante 1: ___ (tema: ___)",
    "Integrante 2: ___ (tema: ___)",
]

ABOUT_TITLE = "Abdução no Mar: Submarino x Disco Voador (Computação Gráfica, UNIPAC 2026/02)"
ABOUT_TEXT = """Submarino emerge no mar noturno e é abduzido por um disco voador.

Sequência: Submerso, Emergindo, Detecção, Posicionamento,
Inspeção, Feixe, Abdução, Final.

Técnicas: hierarquia e transformações, delta time, câmera,
UV, luz lunar com sombras (PCF), água procedural e bloom."""

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
BEAM_OUTER_ALPHA = 0.72
BEAM_CORE_ALPHA = 0.95

# Luzes pontuais dinâmicas (máximo efetivo vem do perfil de qualidade)
SUB_PORTHOLE_LIGHT_STRENGTH = 1.45
SUB_PORTHOLE_LIGHT_RANGE = 6.5
SUB_SEARCHLIGHT_STRENGTH = 1.70
SUB_SEARCHLIGHT_RANGE = 10.0
UFO_GLOW_LIGHT_STRENGTH = 1.15
UFO_GLOW_LIGHT_RANGE = 9.0
UFO_BEAM_LIGHT_STRENGTH = 3.20
UFO_BEAM_LIGHT_RANGE = 15.0

# Anel de impacto do feixe na superfície
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
