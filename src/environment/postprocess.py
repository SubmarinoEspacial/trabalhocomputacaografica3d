"""Pós-processamento noturno: framebuffer de cor, bloom e vinheta."""
from OpenGL.GL import (
    GL_BLEND,
    GL_CLAMP_TO_EDGE,
    GL_COLOR_ATTACHMENT0,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_ATTACHMENT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_COMPONENT24,
    GL_DEPTH_TEST,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_QUADS,
    GL_RENDERBUFFER,
    GL_RGBA,
    GL_RGBA8,
    GL_TEXTURE0,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_UNSIGNED_BYTE,
    glActiveTexture,
    glBegin,
    glBindFramebuffer,
    glBindRenderbuffer,
    glBindTexture,
    glCheckFramebufferStatus,
    glClear,
    glClearColor,
    glDisable,
    glDrawBuffer,
    glEnable,
    glEnd,
    glFramebufferRenderbuffer,
    glFramebufferTexture2D,
    glGenFramebuffers,
    glGenRenderbuffers,
    glGenTextures,
    glGetUniformLocation,
    glLoadIdentity,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glReadBuffer,
    glRenderbufferStorage,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glUniform1f,
    glUniform1i,
    glUniform2f,
    glUniform3f,
    glUseProgram,
    glVertex2f,
    glViewport,
)

from src import config as C
from src.environment.effects import _construir_programa


class ColorRenderTarget:
    """Framebuffer com textura RGBA e depth buffer próprios."""

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self.framebuffer = glGenFramebuffers(1)
        self.color_texture = glGenTextures(1)
        self.depth_buffer = glGenRenderbuffers(1)

        glBindTexture(GL_TEXTURE_2D, self.color_texture)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA8,
            self.width,
            self.height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            None,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glBindTexture(GL_TEXTURE_2D, 0)

        glBindRenderbuffer(GL_RENDERBUFFER, self.depth_buffer)
        glRenderbufferStorage(
            GL_RENDERBUFFER,
            GL_DEPTH_COMPONENT24,
            self.width,
            self.height,
        )
        glBindRenderbuffer(GL_RENDERBUFFER, 0)

        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            self.color_texture,
            0,
        )
        glFramebufferRenderbuffer(
            GL_FRAMEBUFFER,
            GL_DEPTH_ATTACHMENT,
            GL_RENDERBUFFER,
            self.depth_buffer,
        )
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f"Framebuffer de cor incompleto: 0x{status:x}")

    def bind(self):
        """Seleciona o framebuffer e limpa cor/profundidade no tamanho da janela."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glViewport(0, 0, self.width, self.height)
        glClearColor(*C.SKY_COLOR)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    @staticmethod
    def unbind():
        """Volta a desenhar no framebuffer padrão da janela."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)


class PostProcessMaterial:
    """Shader de tela cheia que aplica bloom e grade frio à cena."""

    def __init__(self, width, height):
        self.program = _construir_programa("postprocess.vert", "postprocess.frag")
        self.texel_width = 1.0 / float(max(1, width))
        self.texel_height = 1.0 / float(max(1, height))
        nomes = (
            "u_scene_texture", "u_texel_size", "u_bloom_strength",
            "u_bloom_threshold", "u_vignette_strength", "u_cool_tint",
            "u_bloom_enabled",
        )
        self.uniforms = {
            nome: glGetUniformLocation(self.program, nome) for nome in nomes
        }

    def apply(self, texture_id):
        """Ativa a textura da cena e envia os parâmetros do passe final."""
        glUseProgram(self.program)
        uniform = self.uniforms
        glUniform1i(uniform["u_scene_texture"], 0)
        glUniform2f(uniform["u_texel_size"], self.texel_width, self.texel_height)
        glUniform1f(uniform["u_bloom_strength"], C.POST_BLOOM_STRENGTH)
        glUniform1f(uniform["u_bloom_threshold"], C.POST_BLOOM_THRESHOLD)
        glUniform1i(uniform["u_bloom_enabled"], int(C.POST_BLOOM_ENABLED))
        glUniform1f(uniform["u_vignette_strength"], C.POST_VIGNETTE_STRENGTH)
        glUniform3f(uniform["u_cool_tint"], *C.POST_COOL_TINT)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glDisable(GL_BLEND)

    def unapply(self):
        """Desativa o programa após o quad de tela cheia."""
        glUseProgram(0)


class PostProcess:
    """Renderiza a cena em textura e depois aplica o passe cinematográfico."""

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self.target = ColorRenderTarget(self.width, self.height)
        self.material = PostProcessMaterial(self.width, self.height)

    def begin(self):
        """Inicia o desenho da cena no framebuffer de cor."""
        self.target.bind()

    def end(self):
        """Volta à janela e desenha o quad final com a textura da cena."""
        self.target.unbind()
        glViewport(0, 0, self.width, self.height)
        self.material.apply(self.target.color_texture)

        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        self.material.unapply()
