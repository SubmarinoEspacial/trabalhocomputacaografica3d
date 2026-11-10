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
    GL_TEXTURE1,
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
    glDeleteFramebuffers,
    glDeleteRenderbuffers,
    glDeleteTextures,
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

    def release(self):
        """Libera FBO, textura e depth buffer ao trocar a resolução."""
        glDeleteFramebuffers(1, [self.framebuffer])
        glDeleteTextures(1, [self.color_texture])
        glDeleteRenderbuffers(1, [self.depth_buffer])


class BloomRenderTarget:
    """Framebuffer de cor sem depth, usado pelo bloom em 1/4 de resolução."""

    def __init__(self, width, height):
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.framebuffer = glGenFramebuffers(1)
        self.color_texture = glGenTextures(1)

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

        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glFramebufferTexture2D(
            GL_FRAMEBUFFER,
            GL_COLOR_ATTACHMENT0,
            GL_TEXTURE_2D,
            self.color_texture,
            0,
        )
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        glReadBuffer(GL_COLOR_ATTACHMENT0)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        if status != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError(f"Framebuffer de bloom incompleto: 0x{status:x}")

    def bind(self):
        """Seleciona o alvo reduzido e limpa a cor anterior."""
        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
        glViewport(0, 0, self.width, self.height)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

    def release(self):
        """Libera recursos ao trocar a resolução interna."""
        glDeleteFramebuffers(1, [self.framebuffer])
        glDeleteTextures(1, [self.color_texture])


class BloomPipeline:
    """Extrai e desfoca o bloom em 1/4 da resolução, com dois alvos ping-pong."""

    def __init__(self, target_width, target_height):
        self.bright_program = _construir_programa("postprocess.vert", "bloom_bright.frag")
        self.blur_program = _construir_programa("postprocess.vert", "bloom_blur.frag")
        self.bright_uniforms = {
            nome: glGetUniformLocation(self.bright_program, nome)
            for nome in ("u_scene_texture", "u_source_texel", "u_threshold")
        }
        self.blur_uniforms = {
            nome: glGetUniformLocation(self.blur_program, nome)
            for nome in ("u_texture", "u_texel", "u_direction")
        }
        self.width = 0
        self.height = 0
        self.alvo_a = None
        self.alvo_b = None
        self.resize(target_width, target_height)

    def resize(self, target_width, target_height):
        """Recria os alvos reduzidos apenas quando o tamanho muda."""
        largura = max(1, int(target_width) // 4)
        altura = max(1, int(target_height) // 4)
        if largura == self.width and altura == self.height:
            return
        if self.alvo_a is not None:
            self.alvo_a.release()
            self.alvo_b.release()
        self.width = largura
        self.height = altura
        self.alvo_a = BloomRenderTarget(largura, altura)
        self.alvo_b = BloomRenderTarget(largura, altura)

    @staticmethod
    def _desenhar_quad():
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

    def render(self, scene_texture, source_texel):
        """Executa brilho + desfoque H/V e devolve a textura final do halo."""
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        self.alvo_a.bind()
        glUseProgram(self.bright_program)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, scene_texture)
        glUniform1i(self.bright_uniforms["u_scene_texture"], 0)
        glUniform2f(self.bright_uniforms["u_source_texel"], *source_texel)
        glUniform1f(self.bright_uniforms["u_threshold"], C.POST_BLOOM_THRESHOLD)
        self._desenhar_quad()

        textura_horizontal = self.alvo_a.color_texture
        self.alvo_b.bind()
        glUseProgram(self.blur_program)
        glBindTexture(GL_TEXTURE_2D, textura_horizontal)
        glUniform1i(self.blur_uniforms["u_texture"], 0)
        glUniform2f(
            self.blur_uniforms["u_texel"],
            1.0 / float(self.width),
            1.0 / float(self.height),
        )
        glUniform2f(self.blur_uniforms["u_direction"], 1.0, 0.0)
        self._desenhar_quad()

        self.alvo_a.bind()
        glBindTexture(GL_TEXTURE_2D, self.alvo_b.color_texture)
        glUniform2f(self.blur_uniforms["u_direction"], 0.0, 1.0)
        self._desenhar_quad()

        glUseProgram(0)
        return self.alvo_a.color_texture


class PostProcessMaterial:
    """Shader de tela cheia que compõe cena, bloom reduzido e grade frio."""

    def __init__(self):
        self.program = _construir_programa("postprocess.vert", "postprocess.frag")
        nomes = (
            "u_scene_texture", "u_bloom_texture", "u_bloom_strength",
            "u_vignette_strength", "u_cool_tint", "u_bloom_enabled",
        )
        self.uniforms = {
            nome: glGetUniformLocation(self.program, nome) for nome in nomes
        }

    def apply(self, texture_id, bloom_texture):
        """Ativa cena/bloom e envia os parâmetros do passe final."""
        glUseProgram(self.program)
        uniform = self.uniforms
        glUniform1i(uniform["u_scene_texture"], 0)
        glUniform1i(uniform["u_bloom_texture"], 1)
        glUniform1f(uniform["u_bloom_strength"], C.POST_BLOOM_STRENGTH)
        glUniform1i(uniform["u_bloom_enabled"], int(C.POST_BLOOM_ENABLED))
        glUniform1f(uniform["u_vignette_strength"], C.POST_VIGNETTE_STRENGTH)
        glUniform3f(uniform["u_cool_tint"], *C.POST_COOL_TINT)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, bloom_texture)
        glActiveTexture(GL_TEXTURE0)
        glDisable(GL_BLEND)

    def unapply(self):
        """Desativa o programa após o quad de tela cheia."""
        glUseProgram(0)


class PostProcess:
    """Renderiza a cena em textura e depois aplica o passe cinematográfico."""

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        self.render_scale = min(1.0, max(0.1, float(C.RENDER_SCALE)))
        self.target_width = max(1, int(round(self.width * self.render_scale)))
        self.target_height = max(1, int(round(self.height * self.render_scale)))
        self.target = ColorRenderTarget(self.target_width, self.target_height)
        self.bloom = BloomPipeline(self.target_width, self.target_height)
        self.material = PostProcessMaterial()

    def resize(self, width, height):
        """Recria apenas o framebuffer de cor após resize/tela cheia."""
        self.width = int(width)
        self.height = int(height)
        self.target_width = max(1, int(round(self.width * self.render_scale)))
        self.target_height = max(1, int(round(self.height * self.render_scale)))
        self.target.release()
        self.target = ColorRenderTarget(self.target_width, self.target_height)
        self.bloom.resize(self.target_width, self.target_height)

    def set_render_scale(self, scale):
        """Troca a resolução interna em runtime; só recria o FBO se mudou."""
        scale = min(1.0, max(0.1, float(scale)))
        if abs(scale - self.render_scale) < 1e-4:
            return
        self.render_scale = scale
        self.resize(self.width, self.height)

    def begin(self):
        """Inicia o desenho da cena no framebuffer de cor."""
        self.target.bind()

    def end(self):
        """Volta à janela e desenha o quad final com cena + bloom reduzido."""
        self.target.unbind()
        bloom_texture = 0
        if C.POST_BLOOM_ENABLED:
            bloom_texture = self.bloom.render(
                self.target.color_texture,
                (1.0 / float(self.target_width), 1.0 / float(self.target_height)),
            )
            # O último blur deixa seu FBO vinculado; volte à janela antes do
            # passe final (senão cena/HUD seriam desenhados no alvo reduzido).
            self.target.unbind()
        glViewport(0, 0, self.width, self.height)
        self.material.apply(self.target.color_texture, bloom_texture)

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
