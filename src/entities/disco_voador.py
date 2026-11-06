"""Disco voador estilizado composto por geometrias do framework local."""
import math
import numpy as np
from core.mesh import Mesh
from core.object3d import Object3D
from geometry.primitives import ConeGeometry, SphereGeometry
from material.phong import PhongMaterial
from src import config as C


class DiscoVoador:
    def __init__(self):
        self.root = None
        self.anel = None          # pivô do anel de luzes (gira)
        self.feixe = None         # cone/cilindro do feixe (filho do disco)
        self.reset()

    def reset(self):
        self.position = np.array(C.DISC_START, dtype=float)
        self.hover_phase = 0.0
        self.ring_angle = 0.0
        self.beam_amount = 0.0    # 0 = desligado, 1 = totalmente ligado

    @property
    def hover_offset(self):
        return C.DISC_HOVER_AMP * math.sin(self.hover_phase)

    def build(self, lighting):
        """Monta corpo achatado, cúpula, anel luminoso e feixe retrátil."""
        if self.root is not None:
            return self.root

        material_corpo = PhongMaterial(lighting, (0.42, 0.54, 0.62))
        material_cupula = PhongMaterial(lighting, (0.18, 0.72, 0.82))
        material_anel = PhongMaterial(lighting, (0.92, 0.62, 0.16))
        material_luzes = (
            PhongMaterial(lighting, (0.96, 0.22, 0.16)),
            PhongMaterial(lighting, (0.18, 0.9, 0.58)),
            PhongMaterial(lighting, (0.2, 0.62, 0.98)),
            PhongMaterial(lighting, (0.98, 0.86, 0.32)),
        )
        material_feixe = PhongMaterial(
            lighting,
            (0.24, 0.68, 0.9),
            alpha=0.32,
            emissive=(0.08, 0.24, 0.34),
            transparent=True,
            casts_shadow=False,
        )

        self.root = Object3D()
        self.corpo = Object3D()
        self.corpo.add(
            Mesh(
                SphereGeometry(segments=32, rings=16),
                material_corpo,
                scale=(1.7, 0.34, 1.35),
            )
        )

        cupula = Mesh(
            SphereGeometry(segments=24, rings=12),
            material_cupula,
            position=(0.0, 0.31, 0.0),
            scale=(0.62, 0.48, 0.62),
        )

        # O pivô é filho do corpo, mas este nó não tem escala para não achatar o anel.
        self.anel = Object3D(position=(0.0, 0.08, 0.0))
        self.anel.add(
            Mesh(
                SphereGeometry(segments=24, rings=12),
                material_anel,
                scale=(1.48, 0.09, 1.48),
            )
        )
        for index in range(8):
            angulo = 2.0 * math.pi * index / 8.0
            self.anel.add(
                Mesh(
                    SphereGeometry(segments=10, rings=6),
                    material_luzes[index % len(material_luzes)],
                    position=(1.55 * math.cos(angulo), 0.04, 1.55 * math.sin(angulo)),
                    scale=(0.15, 0.15, 0.15),
                )
            )
        self.corpo.add(cupula, self.anel)

        self.feixe = Mesh(
            ConeGeometry(radius=0.82, height=2.8, segments=32),
            material_feixe,
            position=(0.0, -1.52, 0.0),
        )
        self.root.add(self.corpo, self.feixe)
        self.apply()
        return self.root

    def apply(self):
        """Aplica flutuação, rotação do anel e estado visual do feixe."""
        if self.root is None:
            return

        self.root.setPosition(
            float(self.position[0]),
            float(self.position[1] + self.hover_offset),
            float(self.position[2]),
        )
        if self.anel is not None:
            self.anel.setRotation(0.0, math.degrees(self.ring_angle), 0.0)

        if self.feixe is not None:
            amount = max(0.0, min(1.0, float(self.beam_amount)))
            self.feixe.visible = amount > 0.0
            self.feixe.setScale(amount, amount, amount)
            self.feixe.material.alpha = 0.32 * amount
            self.feixe.material.emissive = (0.08 * amount, 0.24 * amount, 0.34 * amount)
