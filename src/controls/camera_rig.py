"""Rig de câmera controlado pelo teclado, adaptado para a Base local.

Fonte conceitual: Stemkoski e Pascale (2022), capítulo 4, seção "Scene Graph
Framework", classe MovementRig. Esta implementação em Python é uma adaptação.

Estrutura (rig de voo, sem roll):
  1) rig (pai): guarda posição e YAW, girando só em torno do eixo Y do mundo;
  2) câmera (filha): guarda só o PITCH, girando em torno do eixo X local.
A matriz de visão equivalente é Rx(-pitch) · Ry(-yaw) · T(-posição), porque o
MODELVIEW usa pós-multiplicação; a orientação da câmera no mundo é o inverso
Rx(+pitch) · Ry(+yaw), sem rolagem.
"""
import math

import pygame
from OpenGL.GL import GL_MODELVIEW, glLoadIdentity, glMatrixMode, glRotatef, glTranslatef

from src import config as C


def calcular_vetores_movimento(yaw_graus, pitch_graus=0.0):
    """Devolve forward/right/up no plano horizontal para um yaw em graus.

    Com a convenção OpenGL, a câmera olha para -Z local e yaw positivo gira o
    olhar para a esquerda. Por isso forward=(-sin,0,-cos) e right=(cos,0,-sin).
    O pitch não inclina o movimento: ele só existe na câmera filha e o voo
    horizontal continua apoiado no y=0.
    """
    yaw = math.radians(float(yaw_graus))
    seno, coseno = math.sin(yaw), math.cos(yaw)
    forward = (-seno, 0.0, -coseno)
    right = (coseno, 0.0, -seno)
    up = (0.0, 1.0, 0.0)
    return forward, right, up


class CameraRig:
    """Move a câmera no plano horizontal e aplica a visão com yaw e pitch."""

    def __init__(self, posicao=None, velocidade=None, velocidade_rotacao=None,
                 yaw=None, pitch=None):
        posicao = posicao if posicao is not None else C.CAMERA_START_POSITION
        self.x, self.y, self.z = (float(componente) for componente in posicao)
        self.yaw = float(C.CAMERA_START_YAW if yaw is None else yaw)
        self.pitch = float(C.CAMERA_START_PITCH if pitch is None else pitch)
        self.velocidade = float(C.CAMERA_MOVE_SPEED if velocidade is None else velocidade)
        self.velocidade_rotacao = float(
            C.CAMERA_TURN_SPEED if velocidade_rotacao is None else velocidade_rotacao
        )

    def reset(self):
        """Restaura posição e orientação iniciais guardadas em config.py."""
        self.x, self.y, self.z = (float(componente) for componente in C.CAMERA_START_POSITION)
        self.yaw = float(C.CAMERA_START_YAW)
        self.pitch = float(C.CAMERA_START_PITCH)

    def update(self, deltaTime, teclas=None):
        """Atualiza posição e orientação usando o tempo real do quadro."""
        if teclas is None:
            teclas = pygame.key.get_pressed()

        frente = float(self._pressionada(teclas, pygame.K_w)) - float(
            self._pressionada(teclas, pygame.K_s)
        )
        lateral = float(self._pressionada(teclas, pygame.K_d)) - float(
            self._pressionada(teclas, pygame.K_a)
        )
        vertical = float(self._pressionada(teclas, pygame.K_q)) - float(
            self._pressionada(teclas, pygame.K_e)
        )

        forward, right, _ = calcular_vetores_movimento(self.yaw, self.pitch)
        # Soma as teclas como vetores, depois normaliza no plano horizontal;
        # assim duas teclas juntas (ex.: W+D) não andam mais rápido na diagonal.
        movimento_x = frente * forward[0] + lateral * right[0]
        movimento_z = frente * forward[2] + lateral * right[2]
        comprimento = math.hypot(movimento_x, movimento_z)
        if comprimento > 1.0:
            movimento_x /= comprimento
            movimento_z /= comprimento

        velocidade = self.velocidade
        if self._shift_pressionado(teclas):
            velocidade *= C.CAMERA_RUN_MULTIPLIER

        delta = float(deltaTime)
        self.x += movimento_x * velocidade * delta
        self.z += movimento_z * velocidade * delta
        self.y += vertical * velocidade * delta

        # Yaw positivo gira o olhar para a esquerda; por isso LEFT soma e RIGHT subtrai.
        giro_horizontal = float(self._pressionada(teclas, pygame.K_LEFT)) - float(
            self._pressionada(teclas, pygame.K_RIGHT)
        )
        giro_vertical = float(self._pressionada(teclas, pygame.K_UP)) - float(
            self._pressionada(teclas, pygame.K_DOWN)
        )
        passo_rotacao = self.velocidade_rotacao * delta
        self.yaw += giro_horizontal * passo_rotacao
        self.pitch = max(
            -C.PITCH_LIMIT,
            min(C.PITCH_LIMIT, self.pitch + giro_vertical * passo_rotacao),
        )

    def apply(self):
        """Aplica a transformação inversa da câmera à matriz de visão OpenGL."""
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # Duas rotações, nunca roll: a filha inclina em X local, o pai gira em Y do mundo.
        glRotatef(-self.pitch, 1.0, 0.0, 0.0)
        glRotatef(-self.yaw, 0.0, 1.0, 0.0)
        glTranslatef(-self.x, -self.y, -self.z)

    @staticmethod
    def _shift_pressionado(teclas):
        """Detecta SHIFT por mods do Pygame; em fakes simples, devolve False."""
        try:
            return bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
        except Exception:
            return False

    @staticmethod
    def _pressionada(teclas, codigo):
        """Consulta teclas do Pygame ou um mapa simples usado em testes."""
        try:
            return bool(teclas[codigo])
        except (IndexError, KeyError):
            return False


# Compatibilidade com o nome histórico usado no restante do projeto.
MovementRig = CameraRig
