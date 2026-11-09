"""Espuma de contato e esteira deixada pelo submarino na superfície."""
import math
from pathlib import Path

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_TEXTURE0,
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
    glUniform2f,
    glUniform3f,
    glUseProgram,
)

from core.mesh import Mesh
from core.object3d import Object3D
from core.texture import Texture
from geometry.primitives import PlaneGeometry
from src import config as C
from src.environment.mar import water_height


class FoamMaterial:
    """Material transparente e emissivo para as manchas de espuma."""

    transparent = True
    casts_shadow = False

    def __init__(
        self,
        texture,
        scale=3.0,
        alpha=0.5,
        radial=True,
        scroll=(0.02, -0.015),
        color=C.FOAM_COLOR,
        brightness=0.9,
    ):
        self.texture = texture
        self.scale = float(scale)
        self.alpha = float(alpha)
        self.radial = 1.0 if radial else 0.0
        self.scroll = tuple(scroll)
        self.color = tuple(color)
        self.brightness = float(brightness)
        self.time = 0.0
        self.program = self._build_program()
        nomes = (
            "u_foam_texture", "u_time", "u_scroll", "u_scale", "u_alpha",
            "u_foam_color", "u_brightness", "u_radial", "u_exposure", "u_gamma",
        )
        self.uniforms = {nome: glGetUniformLocation(self.program, nome) for nome in nomes}

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
            (shader_dir / "foam.vert").read_text(encoding="utf-8"),
        )
        fragment = self._compile(
            GL_FRAGMENT_SHADER,
            (shader_dir / "foam.frag").read_text(encoding="utf-8"),
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
        """Ativa a textura e envia os parâmetros da mancha de espuma."""
        glUseProgram(self.program)
        uniform = self.uniforms
        glUniform1f(uniform["u_time"], self.time)
        glUniform2f(uniform["u_scroll"], *self.scroll)
        glUniform1f(uniform["u_scale"], self.scale)
        glUniform1f(uniform["u_alpha"], self.alpha)
        glUniform3f(uniform["u_foam_color"], *self.color)
        glUniform1f(uniform["u_brightness"], self.brightness)
        glUniform1f(uniform["u_radial"], self.radial)
        glUniform1f(uniform["u_exposure"], C.EXPOSURE)
        glUniform1f(uniform["u_gamma"], C.GAMMA)
        glUniform1i(uniform["u_foam_texture"], 0)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture.textureID)

    def unapply(self):
        """Desativa o programa após desenhar a espuma."""
        glUseProgram(0)


class EspumaSubmarino:
    """Mantém a espuma na superfície, independente da escala da abdução."""

    def __init__(self, scene):
        raiz = Path(__file__).resolve().parents[2]
        textura = Texture(raiz / "assets" / "textures" / "espuma_procedural.png")
        self.contatoMaterial = FoamMaterial(
            textura,
            scale=2.4,
            alpha=C.FOAM_CONTACT_ALPHA,
            radial=True,
            scroll=(0.024, -0.017),
        )
        self.esteiraMaterial = FoamMaterial(
            textura,
            scale=1.65,
            alpha=C.FOAM_WAKE_ALPHA,
            radial=False,
            scroll=(0.018, 0.012),
            brightness=0.78,
        )

        self.root = Object3D()
        self.contato = Mesh(
            PlaneGeometry(3.8, 2.5),
            self.contatoMaterial,
            position=(0.0, 0.0, 0.0),
        )
        self.esteira = Mesh(
            PlaneGeometry(7.4, 2.6),
            self.esteiraMaterial,
            position=(-4.4, -0.005, 0.0),
        )
        self.root.add(self.contato, self.esteira)
        self.root.setCastShadow(False)
        self.root.setReceiveShadow(False)
        scene.add(self.root)

    def update(self, sub, animation_time):
        """Posiciona contato e esteira somente quando a torre está exposta."""
        surface = water_height(sub.position[0], sub.position[2], animation_time)
        altura_torre = (
            sub.position[1] + C.SUB_TOWER_TOP * sub.scale - surface
        )
        visivel = sub.visible and sub.scale > 0.02 and altura_torre > 0.02
        self.root.visible = visivel
        if not visivel:
            return

        intensidade = min(1.0, max(0.0, altura_torre / 0.55))
        intensidade *= min(1.0, sub.scale * 1.4)
        self.contatoMaterial.alpha = C.FOAM_CONTACT_ALPHA * intensidade
        self.esteiraMaterial.alpha = C.FOAM_WAKE_ALPHA * intensidade
        self.contatoMaterial.time = animation_time
        self.esteiraMaterial.time = animation_time

        self.root.setPosition(
            float(sub.position[0]),
            float(surface + 0.035),
            float(sub.position[2]),
        )
        # A esteira fica atrás do eixo +X local do submarino.
        self.root.setRotation(0.0, math.degrees(sub.yaw), 0.0)


def build_espuma(scene):
    """Cria a espuma do submarino e a devolve para atualização por quadro."""
    return EspumaSubmarino(scene)
