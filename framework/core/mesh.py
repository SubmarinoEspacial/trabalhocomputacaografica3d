"""Malha que associa uma geometria a um material do framework local."""
from core.object3d import Object3D


class Mesh(Object3D):
    """Nó gráfico que desenha uma geometria usando seu material."""

    def __init__(self, geometry, material, position=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
        super().__init__(position, rotation, scale)
        self.geometry = geometry
        self.material = material

    def draw(self, render_pass=None):
        """Desenha apenas no passe compatível com alpha e capacidade de sombra."""
        material_transparente = getattr(self.material, "transparent", False)
        if render_pass == "opaque" and material_transparente:
            return
        if render_pass == "transparent" and not material_transparente:
            return
        if render_pass == "shadow" and not self.castShadow:
            return
        lighting = getattr(self.material, "lighting", None)
        if lighting is not None and render_pass != "shadow":
            lighting.setReceiveShadow(self.receiveShadow)

        self.material.apply()
        try:
            self.geometry.draw()
        finally:
            self.material.unapply()