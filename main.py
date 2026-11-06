"""Aplicação de validação da câmera e dos controles da cena de abdução."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "framework"))

import pygame
from OpenGL.GL import (
    GL_MODELVIEW,
    GL_PROJECTION,
    glClearColor,
    glLoadIdentity,
    glMatrixMode,
)
from OpenGL.GLU import gluPerspective

from core.base import Base
from core_ext.scene import Scene
from src.controls.camera_rig import MovementRig
from src.entities.disco_voador import DiscoVoador
from src.entities.submarino import Submarino
from src.environment.tanque import build_tanque
from src.interaction.abducao import AbducaoController
from light.directional import DirectionalLight
from light.ambient import AmbientLight
from light.shadow_map import ShadowMap
from material.lambert import LightingContext


def setup_luz():
    """Cria a única luz direcional e o programa Lambert compartilhado."""
    # O modelo difuso Lambert segue o conceito de iluminação do capítulo 6 do livro.
    # O shader recebe u_light_direction_eye, u_light_ambient e u_light_diffuse.
    # Cada material envia u_material_color e, no piso, u_use_texture/u_texture.
    # A normal perpendicular à face define o difuso pelo produto escalar com a luz.
    # Lambert controla brilho local; ShadowMap abaixo calcula sombra projetada em outro passe.
    luzAmbiente = AmbientLight(color=(0.16, 0.17, 0.19), strength=1.0)
    luzDirecional = DirectionalLight(
        color=(0.92, 0.88, 0.78),
        strength=1.0,
    )
    luzDirecional.setDirection((-0.4, -1.0, -0.3))
    return LightingContext(luzDirecional, luzAmbiente)


class Aplicacao(Base):
    """Controla a câmera, pausa e ciclo de vida da cena sobre a Base."""

    def initialize(self):
        """Cria a projeção, câmera, entidades e controlador da interação."""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(55.0, self.largura / self.altura, 0.1, 200.0)
        glMatrixMode(GL_MODELVIEW)
        glClearColor(0.035, 0.07, 0.09, 1.0)

        self.lighting = setup_luz()
        self.shadow_map = self.lighting.light.enableShadows(self.lighting)
        self.camera_rig = MovementRig(posicao=(0.0, 8.0, 18.0))
        self.camera_rig.pitch = -20.0
        self.scene = Scene()
        build_tanque(self.scene, self.lighting)

        self.submarino = Submarino()
        self.submarino.build(self.lighting)
        assert self.submarino.root is not None
        self.submarino.root.setCastShadow(True)
        self.submarino.root.setReceiveShadow(True)
        self.scene.add(self.submarino.root)
        self.disco = DiscoVoador()
        self.disco.build(self.lighting)
        assert self.disco.root is not None
        assert self.disco.feixe is not None
        self.disco.root.setCastShadow(True)
        self.disco.root.setReceiveShadow(True)
        self.disco.feixe.setCastShadow(False)
        self.disco.feixe.setReceiveShadow(False)
        self.scene.add(self.disco.root)
        self.controlador = AbducaoController(self.submarino, self.disco)

        self.pausado = False
        self._espaco_anterior = False
        self._r_anterior = False

    def update(self):
        """Atualiza controles e cena; renderiza mesmo quando a animação pausa."""
        delta_quadro = self.deltaTime
        teclas = pygame.key.get_pressed()

        espaco_pressionado = bool(teclas[pygame.K_SPACE])
        if espaco_pressionado and not self._espaco_anterior:
            self.pausado = not self.pausado
        self._espaco_anterior = espaco_pressionado

        r_pressionado = bool(teclas[pygame.K_r])
        if r_pressionado and not self._r_anterior:
            self.controlador.reset()
        self._r_anterior = r_pressionado

        # A câmera usa o tempo do quadro, inclusive enquanto a cena está pausada.
        self.camera_rig.update(delta_quadro, teclas)
        self.lighting.setCameraRotation(self.camera_rig.yaw, self.camera_rig.pitch)
        delta_logica = 0.0 if self.pausado else delta_quadro

        if self.submarino.root is not None:
            self.controlador.update(delta_logica)
            self.submarino.apply()
        if self.disco.root is not None:
            self.disco.apply()

        self.shadow_map.render(self.scene, self.camera_rig)
        self.camera_rig.apply()
        self.scene.render()


if __name__ == "__main__":
    Aplicacao()
