"""Aplicação de validação da câmera e dos controles da cena de abdução."""
import math
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
from src import config as C
from src.entities.disco_voador import DiscoVoador
from src.entities.efeitos import EfeitosAbducao
from src.entities.submarino import Submarino
from src.environment.foam import build_espuma
from src.environment.mar import build_mar
from src.environment.night_materials import NoiteLightingContext
from src.environment.point_light import PointLight
from src.environment.postprocess import PostProcess
from src.environment.shadow import ActionShadowMap
from src.environment.sky import build_ceu
from src.interaction.abducao import AbducaoController
from light.directional import DirectionalLight
from light.ambient import AmbientLight


def setup_luz():
    """Cria a luz lunar direcional e o contexto Lambert da atmosfera noturna."""
    # O modelo difuso Lambert segue o conceito de iluminação do capítulo 6 do livro.
    # O shader recebe u_light_direction_eye, u_light_ambient e u_light_diffuse.
    # Cada material envia u_material_color e, no piso, u_use_texture/u_texture.
    # A normal perpendicular à face define o difuso pelo produto escalar com a luz.
    # Lambert controla brilho local; ShadowMap calcula a sombra projetada em outro passe.
    # A luz ambiente azulada simula o céu noturno; a direcional fria representa a lua.
    luzAmbiente = AmbientLight(color=C.AMBIENT_COLOR, strength=C.AMBIENT_STRENGTH)
    luzLunar = DirectionalLight(
        color=C.MOON_COLOR,
        strength=C.MOON_STRENGTH,
    )
    luzLunar.setDirection(C.MOON_DIRECTION)
    return NoiteLightingContext(
        luzLunar,
        luzAmbiente,
        fogColor=C.FOG_COLOR,
        fogStart=C.FOG_START,
        fogEnd=C.FOG_END,
        fogDensity=C.FOG_DENSITY,
        exposure=C.EXPOSURE,
        gamma=C.GAMMA,
    )


class Aplicacao(Base):
    """Controla a câmera, pausa e ciclo de vida da cena sobre a Base."""

    def initialize(self):
        """Cria a projeção, câmera, entidades e controlador da interação."""
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # O domo noturno tem raio 185; um far plane de 300 evita recortá-lo.
        gluPerspective(55.0, self.largura / self.altura, 0.1, 300.0)
        glMatrixMode(GL_MODELVIEW)
        glClearColor(*C.SKY_COLOR)

        self.lighting = setup_luz()
        # O depth map acompanha a ação em vez de ficar preso ao centro do mundo.
        self.shadow_map = ActionShadowMap(self.lighting)
        self.lighting.light.shadowMap = self.shadow_map
        self.lighting.light.shadowCamera = self.shadow_map.shadowCamera
        self.lighting.light.shadowMaterial = self.shadow_map.depthMaterial
        self.lighting.light.shadowRenderTarget = self.shadow_map.target
        self.camera_rig = MovementRig(posicao=(0.0, 13.0, 34.0))
        self.camera_rig.pitch = -17.0
        self.postprocess = PostProcess(self.largura, self.altura)
        self.scene = Scene()
        # O céu entra primeiro no passe opaco para servir de fundo do horizonte.
        self.ceu = build_ceu(self.scene)
        self.water_material = build_mar(self.scene, self.lighting)

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
        # A espuma é adicionada depois da água para participar do passe transparente.
        self.espuma = build_espuma(self.scene)
        self.efeitos = EfeitosAbducao(self.scene)
        self.controlador = AbducaoController(self.submarino, self.disco)

        self.pausado = False
        self.tempoAnimacao = 0.0
        self._espaco_anterior = False
        self._r_anterior = False

    def _atualizar_luzes_pontuais(self):
        """Posiciona os porões/holofote do sub e as luzes do disco a cada quadro.

        A conversão mundo->olho reutiliza a transformação de câmera do
        framework, na organização de luzes de Stemkoski e Pascale (2022, cap. 6).
        """
        sub = self.submarino
        disco = self.disco
        frente_x = math.cos(sub.yaw)
        frente_z = -math.sin(sub.yaw)
        escala = max(0.0, sub.scale)
        brilho_sub = min(1.0, escala * 1.4) * (0.70 + 0.30 * sub.glow)
        altura_disco = disco.position[1] + disco.hover_offset

        luzes = (
            PointLight(
                (
                    sub.position[0] + frente_x * 0.10 * escala,
                    sub.position[1] + 0.30 * escala,
                    sub.position[2] + frente_z * 0.10 * escala,
                ),
                C.SUB_PORTHOLE_LIGHT_COLOR,
                C.SUB_PORTHOLE_LIGHT_STRENGTH * brilho_sub,
                C.SUB_PORTHOLE_LIGHT_RANGE,
                enabled=sub.visible and brilho_sub > 0.02,
            ),
            PointLight(
                (
                    sub.position[0] + frente_x * 0.90 * escala,
                    sub.position[1] + 1.05 * escala,
                    sub.position[2] + frente_z * 0.90 * escala,
                ),
                C.SUB_SEARCHLIGHT_COLOR,
                C.SUB_SEARCHLIGHT_STRENGTH * brilho_sub,
                C.SUB_SEARCHLIGHT_RANGE,
                enabled=sub.visible and escala > 0.15,
            ),
            PointLight(
                (
                    disco.position[0],
                    altura_disco - 1.35 * C.DISC_SCALE,
                    disco.position[2],
                ),
                C.UFO_BEAM_LIGHT_COLOR,
                C.UFO_BEAM_LIGHT_STRENGTH * disco.beam_amount,
                C.UFO_BEAM_LIGHT_RANGE,
                enabled=disco.beam_amount > 0.01,
            ),
            PointLight(
                (
                    disco.position[0],
                    altura_disco + 0.10 * C.DISC_SCALE,
                    disco.position[2],
                ),
                C.UFO_GLOW_LIGHT_COLOR,
                C.UFO_GLOW_LIGHT_STRENGTH,
                C.UFO_GLOW_LIGHT_RANGE,
                enabled=disco.root is not None and disco.root.visible,
            ),
        )
        self.lighting.set_point_lights(luzes, self.camera_rig)

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
        self.ceu.update(self.camera_rig)
        self.lighting.setCameraRotation(self.camera_rig.yaw, self.camera_rig.pitch)
        delta_logica = 0.0 if self.pausado else delta_quadro
        self.tempoAnimacao += delta_logica
        self.water_material.setTime(self.tempoAnimacao)

        if self.submarino.root is not None:
            self.controlador.update(delta_logica, self.tempoAnimacao)
            self.submarino.apply(self.tempoAnimacao)
            self.espuma.update(self.submarino, self.tempoAnimacao)
        if self.disco.root is not None:
            self.disco.apply()
        self.efeitos.update(self.disco, self.tempoAnimacao)
        self._atualizar_luzes_pontuais()

        # O foco da sombra usa as posições lógicas, antes de desenhar a cena.
        self.shadow_map.updateFocus(delta_quadro, self.submarino, self.disco)
        self.shadow_map.render(self.scene, self.camera_rig)
        # A cena é desenhada em textura e depois recebe bloom/vinheta na janela.
        self.postprocess.begin()
        self.camera_rig.apply()
        self.scene.render()
        self.postprocess.end()


if __name__ == "__main__":
    Aplicacao()
