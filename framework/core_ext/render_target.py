"""Framebuffer com textura de profundidade para shadow mapping."""
from OpenGL.GL import (
    GL_CLAMP_TO_BORDER,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_COMPONENT,
    GL_DEPTH_COMPONENT24,
    GL_FLOAT,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_NEAREST,
    GL_NONE,
    GL_TEXTURE_2D,
    GL_TEXTURE_BORDER_COLOR,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    glBindFramebuffer,
    glBindTexture,
    glCheckFramebufferStatus,
    glDrawBuffer,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenTextures,
    glReadBuffer,
    glTexImage2D,
    glTexParameterfv,
    glTexParameteri,
)


class DepthRenderTarget:
    """Armazena apenas profundidade, sem attachment de cor."""

    def __init__(self, width=1536, height=1536):
        self.width = width
        self.height = height
        self.framebuffer = glGenFramebuffers(1)
        self.depth_texture = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_DEPTH_COMPONENT24,
            self.width,
            self.height,
            0,
            GL_DEPTH_COMPONENT,
            GL_FLOAT,
            None,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, (1.0, 1.0, 1.0, 1.0))

        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_DEPTH_ATTACHMENT,
            GL_TEXTURE_2D,
            self.depth_texture,
            0,
        )
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, 0)

        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f"Framebuffer de profundidade incompleto: 0x{status:x}")

    def bind(self):
        """Seleciona o framebuffer de profundidade para renderização."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

    @staticmethod
    def unbind():
        """Retorna ao framebuffer padrão da janela."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)