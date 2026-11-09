"""Sombra lunar com câmera ortográfica centrada no ponto de interesse.

O framework usa um alvo fixo em (0, 1.5, 0). Aqui o mesmo cálculo é adaptado
para seguir o submarino e o disco, mantendo a sombra nítida durante a abdução.
Fonte conceitual: seção 6.9 de Stemkoski e Pascale (2022).
"""
import numpy as np

from light.shadow_map import ShadowCamera, ShadowMap, _camera_view_matrix
from src import config as C


class ActionShadowCamera(ShadowCamera):
    """Câmera da luz que troca o alvo fixo pelo centro da ação."""

    def __init__(self, ortho_size=C.SHADOW_ORTHO_SIZE, near=1.0, far=100.0):
        super().__init__(ortho_size, near, far)
        self.target = np.array((0.0, C.WATER_LEVEL, 0.0), dtype=float)
        self.distance = 48.0

    def set_target(self, target):
        """Define o ponto médio que a luz ortográfica deve enquadrar."""
        self.target = np.asarray(target, dtype=float)

    def setTarget(self, target):
        """Alias camelCase para o centro do volume de sombra."""
        self.set_target(target)

    def getMatrices(self, direction, camera):
        """Monta projeção e visão da lua sem depender do alvo fixo do framework."""
        direction = np.asarray(direction, dtype=float)
        target = self.target
        light_position = target - direction * self.distance

        forward = target - light_position
        forward /= np.linalg.norm(forward)
        up_reference = np.array((0.0, 1.0, 0.0), dtype=float)
        right = np.cross(forward, up_reference)
        right /= np.linalg.norm(right)
        up = np.cross(right, forward)

        light_view = np.identity(4, dtype=float)
        light_view[0, :3] = right
        light_view[1, :3] = up
        light_view[2, :3] = -forward
        light_view[0, 3] = -np.dot(right, light_position)
        light_view[1, 3] = -np.dot(up, light_position)
        light_view[2, 3] = np.dot(forward, light_position)

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
        # A matriz final transforma diretamente do espaço do olhar para o clip da luz.
        return (
            light_projection,
            light_view,
            light_view_projection @ np.linalg.inv(camera_view),
        )


class ActionShadowMap(ShadowMap):
    """Depth map lunar que acompanha o submarino e o disco voador."""

    def __init__(
        self,
        lighting,
        resolution=C.SHADOW_RESOLUTION,
        ortho_size=C.SHADOW_ORTHO_SIZE,
        bias=C.SHADOW_BIAS,
        follow_speed=C.SHADOW_FOLLOW_SPEED,
    ):
        super().__init__(lighting, resolution, ortho_size, bias)
        self.shadowCamera = ActionShadowCamera(ortho_size)
        self.followSpeed = float(follow_speed)
        self.focus = np.array((0.0, C.WATER_LEVEL, 0.0), dtype=float)
        self._focus_ready = False

    def update_focus(self, dt, sub, disc):
        """Suaviza o alvo entre o submarino e o disco, priorizando a ação."""
        sub_position = np.asarray(sub.position, dtype=float)
        disc_position = np.asarray(disc.position, dtype=float)
        separacao = float(np.linalg.norm((disc_position - sub_position)[[0, 2]]))
        # Quando o disco está próximo, ele divide o enquadramento com o submarino.
        peso_disco = 0.40 if separacao < C.DETECT_RADIUS * 1.5 else 0.18
        target = sub_position + (disc_position - sub_position) * peso_disco
        target[1] = max(
            target[1] + C.SHADOW_FOCUS_HEIGHT,
            C.WATER_LEVEL + 0.8,
        )

        if not self._focus_ready:
            self.focus = target
            self._focus_ready = True
        else:
            # O mesmo raciocínio de suavização exponencial usado em animações com dt.
            alpha = 1.0 - np.exp(-self.followSpeed * max(dt, 0.0))
            self.focus += (target - self.focus) * alpha
        self.shadowCamera.set_target(self.focus)

    def updateFocus(self, dt, sub, disc):
        """Alias camelCase para atualizar o centro do volume de sombra."""
        self.update_focus(dt, sub, disc)
