"""Malha que associa uma geometria a um material do framework local."""
from framework.core.object3d import Object3D


class Mesh(Object3D):
    """Nó gráfico que desenha uma geometria usando seu material."""

    def __init__(self, geometry, material, position=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
        super().__init__(position, rotation, scale)
        self.geometry = geometry
        self.material = material

    def draw(self):
        self.material.apply()
        try:
            self.geometry.draw()
        finally:
            self.material.unapply()