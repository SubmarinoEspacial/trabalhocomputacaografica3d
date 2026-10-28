"""Controles de câmera e pausa (R4).

Sugestão de teclas (documentar no README):
  W/A/S/D mover a câmera, Q/E subir/descer, setas girar,
  ESPAÇO pausar/retomar, R reiniciar a cena
"""
"""Rig de câmera controlado pelo teclado, adaptado para a Base local.

Fonte conceitual: Stemkoski e Pascale (2022), capítulo 4, seção "Scene Graph
Framework", classe MovementRig. Esta implementação em Python é uma adaptação.
"""
import math

import pygame
from OpenGL.GL import GL_MODELVIEW, glLoadIdentity, glMatrixMode, glRotatef, glTranslatef


class MovementRig:
  """Move a câmera em seu plano horizontal e aplica sua transformação de visão."""

  def __init__(self, posicao=(0.0, 1.0, 12.0), velocidade=8.0, velocidade_rotacao=90.0):
    self.x, self.y, self.z = posicao
    self.yaw = 0.0
    self.pitch = 0.0
    self.velocidade = velocidade
    self.velocidade_rotacao = velocidade_rotacao

  def update(self, delta_time, teclas=None):
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

    comprimento = math.hypot(frente, lateral)
    if comprimento > 1.0:
      frente /= comprimento
      lateral /= comprimento

    angulo_yaw = math.radians(self.yaw)
    self.x += self.velocidade * delta_time * (
      lateral * math.cos(angulo_yaw) + frente * math.sin(angulo_yaw)
    )
    self.y += self.velocidade * delta_time * vertical
    self.z += self.velocidade * delta_time * (
      lateral * math.sin(angulo_yaw) - frente * math.cos(angulo_yaw)
    )

    giro_horizontal = float(self._pressionada(teclas, pygame.K_RIGHT)) - float(
      self._pressionada(teclas, pygame.K_LEFT)
    )
    giro_vertical = float(self._pressionada(teclas, pygame.K_UP)) - float(
      self._pressionada(teclas, pygame.K_DOWN)
    )
    passo_rotacao = self.velocidade_rotacao * delta_time
    self.yaw += giro_horizontal * passo_rotacao
    self.pitch = max(
      -85.0,
      min(85.0, self.pitch + giro_vertical * passo_rotacao),
    )

  def apply(self):
    """Aplica a transformação inversa da câmera à matriz de visão OpenGL."""
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glRotatef(-self.pitch, 1.0, 0.0, 0.0)
    glRotatef(-self.yaw, 0.0, 1.0, 0.0)
    glTranslatef(-self.x, -self.y, -self.z)

  @staticmethod
  def _pressionada(teclas, codigo):
    """Consulta teclas do Pygame ou um mapa simples usado em testes."""
    try:
      return bool(teclas[codigo])
    except (IndexError, KeyError):
      return False
