"""Domo de céu noturno com estrelas procedurais e disco lunar.

O domo usa uma esfera do framework e um shader próprio. A direção do céu vem
da normal radial, o que evita depender de coordenadas UV que a esfera não envia.
"""
from pathlib import Path

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_TEXTURE0,
    GL_TEXTURE2,
    GL_TEXTURE_2D,
    GL_VERTEX_SHADER,
    glActiveTexture,
    glAttachShader,
    glBindTexture,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
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

from core.mesh import Mesh
from core.texture import Texture
from geometry.primitives import SphereGeometry
from src import config as C


class SkyMaterial:
    """Material emissivo do domo: gradiente, estrelas e lua no mesmo programa."""

    transparent = False
    casts_shadow = False

    def __init__(self):
        self.program = self._build_program()
        nomes = (
            "u_sky_zenith", "u_sky_horizon", "u_sky_ground",
            "u_star_intensity", "u_stars",
            "u_moon_direction", "u_moon_color", "u_moon_angular_radius",
            "u_moon_texture", "u_exposure", "u_gamma",
        )
        self.uniforms = {nome: glGetUniformLocation(self.program, nome) for nome in nomes}

        raiz = Path(__file__).resolve().parents[2]
        self.star_texture = Texture(
            raiz / "assets" / "textures" / "ceu_estrelado_procedural.png"
        )
        self.moon_texture = Texture(
            raiz / "assets" / "textures" / "lua_procedural.png"
        )
        self._moon_direction = tuple(C.MOON_DIRECTION)

    @staticmethod
    def _compile(shader_type, source):
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

    def _build_program(self):
        shader_dir = Path(__file__).resolve().parents[2] / "shaders"
        vertex = self._compile(
            GL_VERTEX_SHADER,
            (shader_dir / "sky.vert").read_text(encoding="utf-8"),
        )
        fragment = self._compile(
            GL_FRAGMENT_SHADER,
            (shader_dir / "sky.frag").read_text(encoding="utf-8"),
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

    def apply(self):
        """Envia gradiente, texturas e parâmetros lunares antes do domo."""
        glUseProgram(self.program)
        uniform = self.uniforms
        glUniform3f(uniform["u_sky_zenith"], *C.SKY_ZENITH_COLOR)
        glUniform3f(uniform["u_sky_horizon"], *C.SKY_HORIZON_COLOR)
        glUniform3f(uniform["u_sky_ground"], *C.SKY_GROUND_COLOR)
        glUniform1f(uniform["u_star_intensity"], C.STAR_INTENSITY)
        glUniform3f(uniform["u_moon_direction"], *self._moon_direction)
        glUniform3f(uniform["u_moon_color"], *C.MOON_COLOR)
        glUniform1f(
            uniform["u_moon_angular_radius"],
            C.MOON_ANGULAR_RADIUS * 3.14159265359 / 180.0,
        )
        glUniform1f(uniform["u_exposure"], C.EXPOSURE)
        glUniform1f(uniform["u_gamma"], C.GAMMA)

        glUniform1i(uniform["u_stars"], 0)
        glUniform1i(uniform["u_moon_texture"], 2)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.star_texture.textureID)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.moon_texture.textureID)
        glActiveTexture(GL_TEXTURE0)

    def unapply(self):
        """Desativa o programa do domo ao final da malha."""
        glUseProgram(0)


class CeuNoturno:
    """Mantém o domo centrado na câmera para parecer infinitamente distante."""

    def __init__(self, scene):
        self.material = SkyMaterial()
        self.root = Mesh(
            SphereGeometry(segments=64, rings=32),
            self.material,
            scale=(185.0, 185.0, 185.0),
        )
        self.root.setCastShadow(False)
        self.root.setReceiveShadow(False)
        scene.add(self.root)

    def update(self, camera):
        """Translada o domo junto da câmera, sem alterar sua orientação."""
        self.root.setPosition(camera.x, camera.y, camera.z)


def build_ceu(scene):
    """Cria o céu noturno e o devolve para atualização por quadro."""
    return CeuNoturno(scene)
