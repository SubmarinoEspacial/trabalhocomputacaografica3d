"""Material de profundidade para o primeiro passe da seção 6.9.

Implementação local da responsabilidade de ShadowMaterial do livro: desenha
somente profundidade no attachment do mapa da luz.
"""
from pathlib import Path

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_VERTEX_SHADER,
    glAttachShader,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glLinkProgram,
    glShaderSource,
    glUseProgram,
)


class DepthMaterial:
    """Compila os shaders depth-only usados pelo passe da câmera da luz."""

    def __init__(self):
        shader_dir = Path(__file__).resolve().parents[2] / "shaders"
        self.program = glCreateProgram()
        shaders = (
            self._compile(
                GL_VERTEX_SHADER,
                (shader_dir / "depth.vert").read_text(encoding="utf-8"),
            ),
            self._compile(
                GL_FRAGMENT_SHADER,
                (shader_dir / "depth.frag").read_text(encoding="utf-8"),
            ),
        )
        for shader in shaders:
            glAttachShader(self.program, shader)
            glDeleteShader(shader)
        glLinkProgram(self.program)
        if not glGetProgramiv(self.program, GL_LINK_STATUS):
            raise RuntimeError(self._decode(glGetProgramInfoLog(self.program)))

    @staticmethod
    def _decode(message):
        return message.decode("utf-8", errors="replace") if isinstance(message, bytes) else str(message)

    @classmethod
    def _compile(cls, shader_type, source):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            raise RuntimeError(cls._decode(glGetShaderInfoLog(shader)))
        return shader

    def activate(self):
        """Seleciona o programa de profundidade para o passe da luz."""
        glUseProgram(self.program)

    @staticmethod
    def deactivate():
        """Retorna ao pipeline padrão após preencher o depth target."""
        glUseProgram(0)