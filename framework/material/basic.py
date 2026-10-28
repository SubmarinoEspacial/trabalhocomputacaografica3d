"""Materiais simples implementados para o framework local do projeto."""
from OpenGL.GL import GL_TEXTURE_2D, glColor3f, glDisable


class ColorMaterial:
    """Material de cor uniforme usado nas paredes do tanque."""

    def __init__(self, color):
        self.color = tuple(color)

    def apply(self):
        glDisable(GL_TEXTURE_2D)
        glColor3f(*self.color)

    def unapply(self):
        pass