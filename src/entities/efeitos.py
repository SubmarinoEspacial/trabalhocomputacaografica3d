"""Efeitos de superfície que acompanham o feixe de abdução."""
from core.mesh import Mesh
from geometry.primitives import PlaneGeometry
from src import config as C
from src.environment.effects import ImpactRingMaterial
from src.environment.mar import water_height


class EfeitosAbducao:
    """Mantém o anel de impacto na superfície, independente da altura do disco."""

    def __init__(self, scene):
        self.material = ImpactRingMaterial()
        self.anel = Mesh(
            PlaneGeometry(C.IMPACT_RING_SIZE, C.IMPACT_RING_SIZE),
            self.material,
        )
        self.anel.setCastShadow(False)
        self.anel.setReceiveShadow(False)
        self.anel.visible = False
        scene.add(self.anel)

    def update(self, disco, animation_time):
        """Posiciona o anel no ponto do mar abaixo do disco e anima as ondas."""
        intensidade = max(0.0, min(1.0, disco.beam_amount))
        self.anel.visible = intensidade > 0.01
        if not self.anel.visible:
            return

        surface = water_height(
            disco.position[0],
            disco.position[2],
            animation_time,
        )
        self.anel.setPosition(
            float(disco.position[0]),
            float(surface + 0.055),
            float(disco.position[2]),
        )
        self.material.time = animation_time
        self.material.set_amount(intensidade)
