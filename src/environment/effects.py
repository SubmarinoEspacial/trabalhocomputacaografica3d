"""Materiais de efeitos aditivos: feixe, impacto e brilhos noturnos."""
from pathlib import Path

from OpenGL.GL import (
    GL_BLEND,
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_ONE,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_SRC_ALPHA,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_VERTEX_SHADER,
    glActiveTexture,
    glAttachShader,
    glBindTexture,
    glBlendFunc,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glEnable,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glUniform1f,
    glUniform1i,
    glUniform3f,
    glUseProgram,
)

from core.texture import Texture
from src import config as C


def _compilar_shader(shader_type, source):
    """Compila um shader e devolve uma mensagem legível em caso de erro."""
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)
    if not glGetShaderiv(shader, GL_COMPILE_STATUS):
        log = glGetShaderInfoLog(shader)
        raise RuntimeError(
            log.decode("utf-8", errors="replace")
            if isinstance(log, bytes)
            else str(log)
        )
    return shader


def _construir_programa(vertex_name, fragment_name):
    """Liga um par de shaders localizado em `shaders/`."""
    shader_dir = Path(__file__).resolve().parents[2] / "shaders"
    vertex = _compilar_shader(
        GL_VERTEX_SHADER,
        (shader_dir / vertex_name).read_text(encoding="utf-8"),
    )
    fragment = _compilar_shader(
        GL_FRAGMENT_SHADER,
        (shader_dir / fragment_name).read_text(encoding="utf-8"),
    )
    program = glCreateProgram()
    glAttachShader(program, vertex)
    glAttachShader(program, fragment)
    glDeleteShader(vertex)
    glDeleteShader(fragment)
    glLinkProgram(program)
    if not glGetProgramiv(program, GL_LINK_STATUS):
        log = glGetProgramInfoLog(program)
        raise RuntimeError(
            log.decode("utf-8", errors="replace")
            if isinstance(log, bytes)
            else str(log)
        )
    return program


class BeamMaterial:
    """Feixe transparente aditivo, animado por textura e intensidade."""

    transparent = True
    casts_shadow = False

    def __init__(
        self,
        texture,
        color=C.BEAM_COLOR,
        intensity=C.BEAM_OUTER_ALPHA,
        height=2.5,
        radius_bottom=1.35,
        radius_top=0.02,
    ):
        if not isinstance(texture, Texture):
            raise TypeError("BeamMaterial requer uma instância de Texture.")
        self.texture = texture
        self.color = tuple(color)
        self.intensity = float(intensity)
        self.height = float(height)
        self.radius_bottom = float(radius_bottom)
        self.radius_top = float(radius_top)
        self.time = 0.0
        self.program = self._build_program()
        nomes = (
            "u_beam_color", "u_intensity", "u_time", "u_noise_texture",
            "u_height", "u_radius_bottom", "u_radius_top",
            "u_exposure", "u_gamma",
        )
        self.uniforms = {nome: glGetUniformLocation(self.program, nome) for nome in nomes}

    def _build_program(self):
        return _construir_programa("beam.vert", "beam.frag")

    def set_amount(self, amount):
        """Atualiza a intensidade do volume conforme o estado da abdução."""
        self.intensity = max(0.0, min(1.0, float(amount)))

    def apply(self):
        """Desenha o feixe com blending aditivo e textura de ruído animada."""
        glUseProgram(self.program)
        uniform = self.uniforms
        glUniform3f(uniform["u_beam_color"], *self.color)
        glUniform1f(uniform["u_intensity"], self.intensity)
        glUniform1f(uniform["u_time"], self.time)
        glUniform1f(uniform["u_height"], self.height)
        glUniform1f(uniform["u_radius_bottom"], self.radius_bottom)
        glUniform1f(uniform["u_radius_top"], self.radius_top)
        glUniform1f(uniform["u_exposure"], C.EXPOSURE)
        glUniform1f(uniform["u_gamma"], C.GAMMA)
        glUniform1i(uniform["u_noise_texture"], 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture.textureID)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    def unapply(self):
        """Restaura o blending padrão usado pelo restante da transparência."""
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(0)


class ImpactRingMaterial:
    """Anel aditivo que marca o ponto onde o feixe toca a superfície do mar."""

    transparent = True
    casts_shadow = False

    def __init__(self, color=C.IMPACT_RING_COLOR, amount=0.0):
        self.color = tuple(color)
        self.amount = float(amount)
        self.time = 0.0
        self.program = _construir_programa("impact.vert", "impact.frag")
        nomes = (
            "u_impact_color", "u_amount", "u_time", "u_exposure", "u_gamma",
        )
        self.uniforms = {
            nome: glGetUniformLocation(self.program, nome) for nome in nomes
        }

    def set_amount(self, amount):
        """Controla a opacidade do anel junto com a intensidade do feixe."""
        self.amount = max(0.0, min(1.0, float(amount))) * C.IMPACT_RING_ALPHA

    def apply(self):
        """Desenha o anel com blending aditivo sobre a água."""
        glUseProgram(self.program)
        uniform = self.uniforms
        glUniform3f(uniform["u_impact_color"], *self.color)
        glUniform1f(uniform["u_amount"], self.amount)
        glUniform1f(uniform["u_time"], self.time)
        glUniform1f(uniform["u_exposure"], C.EXPOSURE)
        glUniform1f(uniform["u_gamma"], C.GAMMA)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    def unapply(self):
        """Restaura o blending padrão após o efeito."""
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glUseProgram(0)
