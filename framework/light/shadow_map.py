"""Dois passes locais de shadow mapping para a luz direcional da cena.

Fonte conceitual: seção 6.9 de Stemkoski e Pascale (2022); sem cópia de código.
"""
from pathlib import Path

import numpy as np
from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_DEPTH_BUFFER_BIT,
    GL_FRAGMENT_SHADER,
    GL_MATRIX_MODE,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_VIEWPORT,
    GL_VERTEX_SHADER,
    glAttachShader,
    glClear,
    glClearDepth,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glGetIntegerv,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glLinkProgram,
    glLoadMatrixf,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glShaderSource,
    glViewport,
    GL_LINK_STATUS,
)

from framework.core_ext.render_target import DepthRenderTarget


class ShadowMap:
    """Gera depth map ortográfico e o entrega ao shader Lambert."""

    def __init__(self, lighting, resolution=2048, ortho_size=26.0, bias=0.0012):
        self.lighting = lighting
        self.resolution = resolution
        self.ortho_size = ortho_size
        self.bias = bias
        self.target = DepthRenderTarget(resolution, resolution)
        self.depth_program = self._build_depth_program()
        self.lighting.set_shadow_map(
            self.target.depth_texture,
            (resolution, resolution),
            bias,
        )

    @staticmethod
    def _compilar_shader(shader_type, source):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            log = glGetShaderInfoLog(shader)
            if isinstance(log, bytes):
                log = log.decode("utf-8", errors="replace")
            raise RuntimeError(f"Falha no shader de profundidade: {log}")
        return shader

    def _build_depth_program(self):
        shader_dir = Path(__file__).resolve().parents[2] / "shaders"
        vertex = self._compilar_shader(
            GL_VERTEX_SHADER,
            (shader_dir / "depth.vert").read_text(encoding="utf-8"),
        )
        fragment = self._compilar_shader(
            GL_FRAGMENT_SHADER,
            (shader_dir / "depth.frag").read_text(encoding="utf-8"),
        )
        program = glCreateProgram()
        glAttachShader(program, vertex)
        glAttachShader(program, fragment)
        glLinkProgram(program)
        glDeleteShader(vertex)
        glDeleteShader(fragment)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            log = glGetProgramInfoLog(program)
            if isinstance(log, bytes):
                log = log.decode("utf-8", errors="replace")
            raise RuntimeError(f"Falha ao vincular shader de profundidade: {log}")
        return program

    def _light_matrices(self, camera):
        """Calcula view/projeção ortográficas e a conversão do olho para a luz."""
        direction = np.asarray(self.lighting.light.direction, dtype=float)
        alvo = np.array((0.0, 1.5, 0.0), dtype=float)
        posicao_luz = alvo - direction * 45.0
        frente = alvo - posicao_luz
        frente /= np.linalg.norm(frente)
        cima_referencia = np.array((0.0, 1.0, 0.0), dtype=float)
        direita = np.cross(frente, cima_referencia)
        direita /= np.linalg.norm(direita)
        cima = np.cross(direita, frente)

        light_view = np.identity(4, dtype=float)
        light_view[0, :3] = direita
        light_view[1, :3] = cima
        light_view[2, :3] = -frente
        light_view[0, 3] = -np.dot(direita, posicao_luz)
        light_view[1, 3] = -np.dot(cima, posicao_luz)
        light_view[2, 3] = np.dot(frente, posicao_luz)

        tamanho = self.ortho_size
        near, far = 1.0, 100.0
        light_projection = np.array(
            (
                (1.0 / tamanho, 0.0, 0.0, 0.0),
                (0.0, 1.0 / tamanho, 0.0, 0.0),
                (0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near)),
                (0.0, 0.0, 0.0, 1.0),
            ),
            dtype=float,
        )
        light_view_projection = light_projection @ light_view

        camera_view = _camera_view_matrix(camera)
        return light_projection, light_view, light_view_projection @ np.linalg.inv(camera_view)

    def render(self, scene, camera):
        """Renderiza a cena da luz e restaura estado para o passe visível."""
        light_projection, light_view, light_matrix_eye = self._light_matrices(camera)
        self.lighting.set_shadow_matrix(light_matrix_eye)

        viewport = tuple(int(value) for value in glGetIntegerv(GL_VIEWPORT))
        matrix_mode = int(glGetIntegerv(GL_MATRIX_MODE))
        self.target.bind()
        glViewport(0, 0, self.resolution, self.resolution)
        glClearDepth(1.0)
        glClear(GL_DEPTH_BUFFER_BIT)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadMatrixf(light_projection.astype(np.float32).flatten(order="F"))
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadMatrixf(light_view.astype(np.float32).flatten(order="F"))

        try:
            self.lighting.begin_depth_pass(self.depth_program)
            scene.render(shadow_pass=True)
        finally:
            self.lighting.end_depth_pass()
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()
            glMatrixMode(matrix_mode)
            self.target.unbind()
            glViewport(*viewport)


def _camera_view_matrix(camera):
    """Replica as rotações/translação que MovementRig aplica no model-view."""
    yaw = np.radians(-camera.yaw)
    pitch = np.radians(-camera.pitch)
    cos_yaw, sin_yaw = np.cos(yaw), np.sin(yaw)
    cos_pitch, sin_pitch = np.cos(pitch), np.sin(pitch)
    rotation_y = np.array(
        ((cos_yaw, 0.0, sin_yaw, 0.0), (0.0, 1.0, 0.0, 0.0), (-sin_yaw, 0.0, cos_yaw, 0.0), (0.0, 0.0, 0.0, 1.0)),
        dtype=float,
    )
    rotation_x = np.array(
        ((1.0, 0.0, 0.0, 0.0), (0.0, cos_pitch, -sin_pitch, 0.0), (0.0, sin_pitch, cos_pitch, 0.0), (0.0, 0.0, 0.0, 1.0)),
        dtype=float,
    )
    x, y, z = camera.x, camera.y, camera.z
    translation = np.array(
        ((1.0, 0.0, 0.0, -x), (0.0, 1.0, 0.0, -y), (0.0, 0.0, 1.0, -z), (0.0, 0.0, 0.0, 1.0)),
        dtype=float,
    )
    return rotation_x @ rotation_y @ translation