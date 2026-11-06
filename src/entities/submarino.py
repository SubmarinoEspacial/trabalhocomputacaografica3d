"""Submarino estilizado composto por geometrias do framework local."""
import math

import numpy as np
from core.mesh import Mesh
from core.object3d import Object3D
from geometry.primitives import BoxGeometry, CylinderGeometry
from material.phong import PhongMaterial
from src import config as C


class Submarino:
    def __init__(self):
        self.root = None          # Object3D raiz (criado em build)
        self.helice = None        # pivô da hélice
        self.reset()

    def reset(self):
        self.position = np.array(C.SUB_START, dtype=float)
        self.yaw = 0.0
        self.scale = 1.0
        self.prop_angle = 0.0
        self.prop_speed = C.PROP_SPEED

    def build(self, lighting):
        """Monta corpo, torre, periscópio, hélice e estabilizadores."""
        if self.root is not None:
            return self.root

        material_casco = PhongMaterial(lighting, (0.08, 0.24, 0.36))
        material_proa = PhongMaterial(lighting, (0.9, 0.66, 0.22))
        material_torre = PhongMaterial(lighting, (0.18, 0.48, 0.57))
        material_periscopio = PhongMaterial(lighting, (0.82, 0.88, 0.78))
        material_helice = PhongMaterial(lighting, (0.84, 0.32, 0.16))
        material_aletas = PhongMaterial(lighting, (0.12, 0.39, 0.48))

        self.root = Object3D()

        # O cilindro local aponta em Y; girá-lo 90 graus em Z alinha o casco a X.
        corpo = Mesh(
            CylinderGeometry(0.72, 0.72, 4.8, segments=24),
            material_casco,
            rotation=(0.0, 0.0, 90.0),
        )
        proa = Mesh(
            CylinderGeometry(0.0, 0.72, 1.2, segments=24),
            material_proa,
            position=(2.75, 0.0, 0.0),
            rotation=(0.0, 0.0, -90.0),
        )

        torre = Object3D(position=(0.25, 0.76, 0.0))
        torre.add(
            Mesh(
                CylinderGeometry(0.38, 0.48, 0.72, segments=16),
                material_torre,
            ),
            Mesh(
                CylinderGeometry(0.07, 0.07, 0.78, segments=12),
                material_periscopio,
                position=(0.08, 0.68, 0.0),
            ),
        )

        # As pás ficam no plano YZ e giram juntas ao redor do eixo X do casco.
        self.helice = Object3D(position=(-2.72, 0.0, 0.0))
        self.helice.add(
            Mesh(
                CylinderGeometry(0.22, 0.22, 0.36, segments=12),
                material_proa,
                rotation=(0.0, 0.0, 90.0),
            )
        )
        for index in range(3):
            self.helice.add(
                Mesh(
                    BoxGeometry(0.12, 0.92, 0.24),
                    material_helice,
                    position=(0.0, 0.43, 0.0),
                    rotation=(index * 120.0, 0.0, 0.0),
                )
            )

        leme = Mesh(
            BoxGeometry(0.82, 0.76, 0.1),
            material_aletas,
            position=(-2.12, 0.52, 0.0),
        )
        aleta_esquerda = Mesh(
            BoxGeometry(0.9, 0.1, 0.82),
            material_aletas,
            position=(-1.95, 0.0, -0.62),
        )
        aleta_direita = Mesh(
            BoxGeometry(0.9, 0.1, 0.82),
            material_aletas,
            position=(-1.95, 0.0, 0.62),
        )
        planos_proa = (
            Mesh(
                BoxGeometry(0.7, 0.1, 0.52),
                material_aletas,
                position=(1.35, 0.0, -0.68),
            ),
            Mesh(
                BoxGeometry(0.7, 0.1, 0.52),
                material_aletas,
                position=(1.35, 0.0, 0.68),
            ),
        )

        self.root.add(
            corpo,
            proa,
            torre,
            self.helice,
            leme,
            aleta_esquerda,
            aleta_direita,
            *planos_proa,
        )
        self.apply()
        return self.root

    def apply(self):
        """Copia o estado de animação para as transformações do modelo."""
        if self.root is None:
            return

        self.root.setPosition(*(float(coordenada) for coordenada in self.position))
        self.root.setRotation(0.0, math.degrees(self.yaw), 0.0)
        self.root.setScale(self.scale, self.scale, self.scale)
        if self.helice is not None:
            self.helice.setRotation(math.degrees(self.prop_angle), 0.0, 0.0)
