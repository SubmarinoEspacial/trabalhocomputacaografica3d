"""Textura OpenGL independente dos materiais que a amostram."""
import pygame
from OpenGL.GL import (
    GL_LINEAR,
    GL_REPEAT,
    GL_RGB,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    glBindTexture,
    glGenTextures,
    glPixelStorei,
    glTexImage2D,
    glTexParameteri,
)


class Texture:
    """Armazena a imagem em GPU e configura repetição e filtro linear."""

    def __init__(self, imagePath, filtering=GL_LINEAR):
        surface = pygame.image.load(str(imagePath))
        self.width, self.height = surface.get_size()
        pixels = pygame.image.tostring(surface, "RGB", True)
        self.textureID = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.textureID)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        # GL_LINEAR interpola texels vizinhos e evita pixelacao no piso em perspectiva.
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filtering)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filtering)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGB,
            self.width,
            self.height,
            0,
            GL_RGB,
            GL_UNSIGNED_BYTE,
            pixels,
        )
        glBindTexture(GL_TEXTURE_2D, 0)