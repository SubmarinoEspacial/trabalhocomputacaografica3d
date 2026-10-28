"""Valida a janela OpenGL com um cubo rotacionado por delta time."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "framework"))

from OpenGL.GL import (
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    glBegin,
    glColor3f,
    glEnd,
    glLoadIdentity,
    glMatrixMode,
    glRotatef,
    glTranslatef,
    glVertex3f,
)
from OpenGL.GLU import gluPerspective

from core.base import Base


class DemoCubo(Base):
    """Desenha um cubo colorido para testar o contexto e o loop OpenGL."""

    def initialize(self):
        """Configura a projeção e inicia o ângulo da animação."""
        proporcao = self.largura / self.altura
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, proporcao, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

        self.angulo = 0.0

    def update(self):
        """Avança a rotação conforme o tempo real e desenha as seis faces."""
        self.angulo = (self.angulo + 90.0 * self.delta_time) % 360.0

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -5.0)
        glRotatef(self.angulo, 1.0, 1.0, 0.0)
        self._desenhar_cubo()

    def _desenhar_cubo(self):
        """Emite os vértices das faces usando o modo imediato do OpenGL."""
        faces = (
            ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)),
            ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1)),
            ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)),
            ((1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1)),
            ((-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1)),
            ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)),
        )
        cores = (
            (0.95, 0.28, 0.22),
            (0.25, 0.75, 0.95),
            (0.35, 0.85, 0.48),
            (0.98, 0.72, 0.22),
            (0.72, 0.42, 0.9),
            (0.95, 0.45, 0.68),
        )

        glBegin(GL_QUADS)
        for cor, vertices in zip(cores, faces):
            glColor3f(*cor)
            for x, y, z in vertices:
                glVertex3f(x, y, z)
        glEnd()


if __name__ == "__main__":
    DemoCubo()
