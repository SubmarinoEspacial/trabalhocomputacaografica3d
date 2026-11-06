"""Dois passes locais de shadow mapping para a luz direcional da cena.

Fonte conceitual: seção 6.9 de Stemkoski e Pascale (2022); sem cópia de código.
"""
import numpy as np
from OpenGL.GL import (
    GL_DEPTH_BUFFER_BIT,
    GL_MATRIX_MODE,
    GL_MODELVIEW,
    GL_PROJECTION,
    GL_VIEWPORT,
    glClear,
    glClearDepth,
    glGetIntegerv,
    glLoadMatrixf,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glViewport,
)

from core_ext.render_target import DepthRenderTarget
from material.depth import DepthMaterial


class ShadowCamera:
    """Câmera ortográfica da luz, equivalente ao ShadowCamera da seção 6.9."""

    def __init__(self, orthoSize=26.0, near=1.0, far=100.0):
        self.setViewRegion(-orthoSize, orthoSize, orthoSize, -orthoSize, near, far)

    def setViewRegion(self, left, right, top, bottom, near, far):
        """Define os limites ortográficos da luz sem mudar a câmera do usuário."""
        self.left = left
        self.right = right
        self.top = top
        self.bottom = bottom
        self.near = near
        self.far = far

    def getMatrices(self, direction, camera):
        """Retorna projeção, view da luz e matriz de clip da luz para o olho."""
        direction = np.asarray(direction, dtype=float)
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

        light_projection = np.array(
            (
                (2.0 / (self.right - self.left), 0.0, 0.0, -(self.right + self.left) / (self.right - self.left)),
                (0.0, 2.0 / (self.top - self.bottom), 0.0, -(self.top + self.bottom) / (self.top - self.bottom)),
                (0.0, 0.0, -2.0 / (self.far - self.near), -(self.far + self.near) / (self.far - self.near)),
                (0.0, 0.0, 0.0, 1.0),
            ),
            dtype=float,
        )
        light_view_projection = light_projection @ light_view
        camera_view = _camera_view_matrix(camera)
        return light_projection, light_view, light_view_projection @ np.linalg.inv(camera_view)


class ShadowMap:
    """Gera depth map ortográfico e o entrega ao shader Lambert."""

    def __init__(self, lighting, resolution=2048, ortho_size=26.0, bias=0.0012):
        self.lighting = lighting
        self.resolution = resolution
        self.bias = bias
        self.shadowCamera = ShadowCamera(ortho_size)
        self.target = DepthRenderTarget(resolution, resolution)
        self.depthMaterial = DepthMaterial()
        self.lighting.setShadowMap(
            self.target.depth_texture,
            (resolution, resolution),
            bias,
        )

    def _light_matrices(self, camera):
        """Delega as matrizes de luz à câmera ortográfica do passe de sombra."""
        return self.shadowCamera.getMatrices(self.lighting.light.direction, camera)

    def render(self, scene, camera):
        """Renderiza a cena da luz e restaura estado para o passe visível."""
        light_projection, light_view, light_matrix_eye = self._light_matrices(camera)
        self.lighting.setShadowMatrix(light_matrix_eye)

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
            self.lighting.beginDepthPass(self.depthMaterial.program)
            scene.render(shadow_pass=True)
        finally:
            self.lighting.endDepthPass()
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