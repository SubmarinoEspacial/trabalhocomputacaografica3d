"""Material de textura repetível combinado com iluminação Lambert.

Implementação própria apoiada no conceito de texture mapping do capítulo 5,
"Textures", de Stemkoski e Pascale (2022); nenhum código do livro foi copiado.
"""
import pygame
from OpenGL.GL import (
    GL_LINEAR,
    GL_RGB,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_REPEAT,
    GL_TEXTURE_2D,
    GL_UNPACK_ALIGNMENT,
    GL_UNSIGNED_BYTE,
    glBindTexture,
    glGenTextures,
    glPixelStorei,
    glTexImage2D,
    glTexParameteri,
)
from framework.material.lambert import LambertMaterial


class TextureMaterial(LambertMaterial):
    """Carrega textura e usa o mesmo shader iluminado dos materiais sólidos."""

    def __init__(self, lighting, image_path):
        surface = pygame.image.load(str(image_path))
        self.width, self.height = surface.get_size()
        pixels = pygame.image.tostring(surface, "RGB", True)
        self.texture_id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
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
        super().__init__(lighting, (1.0, 1.0, 1.0), texture_id=self.texture_id)