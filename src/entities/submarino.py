"""Submarino noturno detalhado, composto apenas com geometrias do framework."""
import math
from pathlib import Path

import numpy as np
from core.mesh import Mesh
from core.object3d import Object3D
from core.texture import Texture
from geometry.primitives import BoxGeometry, CylinderGeometry, SphereGeometry
from material.phong import PhongMaterial
from src import config as C
from src.environment.mar import water_height
from src.environment.night_materials import TexturedPhongMaterial


class Submarino:
    def __init__(self):
        self.root = None          # Object3D raiz (criado em build)
        self.helice = None        # pivô da hélice
        self._glow_materials = ()
        self._night_lights = ()
        self._sem_sombra = ()
        self.reset()

    def reset(self):
        self.position = np.array(C.SUB_START, dtype=float)
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.scale = 1.0
        self.glow = 0.0
        self.waterTime = 0.0
        self.visible = True
        self.castsShadow = False
        self.prop_angle = 0.0
        self.prop_speed = C.PROP_SPEED
        if self.root is not None:
            self.root.visible = True

    def _materiais(self, lighting):
        """Cria os materiais do casco, detalhes metálicos e luzes internas."""
        textura_casco = Texture(
            Path(__file__).resolve().parents[2]
            / "assets"
            / "textures"
            / "pintura_submarino_procedural.png"
        )
        self._hullTexture = textura_casco

        casco = PhongMaterial(
            lighting,
            (0.045, 0.115, 0.145),
            specular=(0.36, 0.44, 0.48),
            shininess=52.0,
            emissive=C.SUB_GLOW_COLOR,
            emissiveStrength=0.0,
        )
        casco_texturizado = TexturedPhongMaterial(
            lighting,
            textura_casco,
            color=(0.88, 0.96, 1.0),
            repeatUV=(2.0, 1.0),
            specular=(0.30, 0.36, 0.40),
            shininess=28.0,
            emissive=C.SUB_GLOW_COLOR,
            emissiveStrength=0.0,
        )
        torre = PhongMaterial(
            lighting,
            (0.055, 0.135, 0.165),
            specular=(0.34, 0.42, 0.46),
            shininess=46.0,
            emissive=C.SUB_GLOW_COLOR,
            emissiveStrength=0.0,
        )
        metal = PhongMaterial(
            lighting,
            (0.20, 0.25, 0.25),
            specular=(0.62, 0.66, 0.64),
            shininess=84.0,
        )
        latao = PhongMaterial(
            lighting,
            (0.38, 0.30, 0.12),
            specular=(0.82, 0.68, 0.30),
            shininess=96.0,
        )
        borracha = PhongMaterial(
            lighting,
            (0.018, 0.024, 0.026),
            specular=(0.12, 0.13, 0.12),
            shininess=18.0,
        )
        helice = PhongMaterial(
            lighting,
            (0.46, 0.31, 0.11),
            specular=(0.95, 0.80, 0.42),
            shininess=110.0,
        )
        janela = PhongMaterial(
            lighting,
            (0.010, 0.045, 0.060),
            emissive=(0.16, 0.62, 0.92),
            emissiveStrength=1.5,
        )
        luz_quente = PhongMaterial(
            lighting,
            (0.08, 0.055, 0.025),
            emissive=(1.0, 0.63, 0.24),
            emissiveStrength=2.0,
        )
        luz_vermelha = PhongMaterial(
            lighting,
            (0.10, 0.010, 0.006),
            emissive=(1.0, 0.06, 0.025),
            emissiveStrength=2.4,
        )
        luz_verde = PhongMaterial(
            lighting,
            (0.008, 0.09, 0.025),
            emissive=(0.04, 1.0, 0.30),
            emissiveStrength=2.4,
        )
        luz_branca = PhongMaterial(
            lighting,
            (0.12, 0.13, 0.14),
            emissive=(0.92, 0.97, 1.0),
            emissiveStrength=2.0,
        )
        holofote = PhongMaterial(
            lighting,
            (0.16, 0.15, 0.12),
            emissive=(1.0, 0.88, 0.58),
            emissiveStrength=2.8,
        )

        self._glow_materials = (casco, casco_texturizado, torre, metal, latao, helice)
        # Base das luzes, acréscimo durante a abdução, frequência e fase do pulso.
        self._night_lights = (
            (janela, 1.5, 1.2, 1.7, 0.0),
            (luz_quente, 2.0, 1.0, 2.2, 0.6),
            (luz_vermelha, 2.4, 1.4, 1.1, 0.0),
            (luz_verde, 2.4, 1.4, 1.1, math.pi),
            (luz_branca, 2.0, 1.2, 1.3, 1.2),
            (holofote, 2.8, 1.8, 0.9, 0.3),
        )
        return {
            "casco": casco,
            "casco_texturizado": casco_texturizado,
            "torre": torre,
            "metal": metal,
            "latao": latao,
            "borracha": borracha,
            "helice": helice,
            "janela": janela,
            "luz_quente": luz_quente,
            "luz_vermelha": luz_vermelha,
            "luz_verde": luz_verde,
            "luz_branca": luz_branca,
            "holofote": holofote,
        }

    def build(self, lighting):
        """Monta casco, torre, acessórios, hélice e luzes de navegação."""
        if self.root is not None:
            return self.root

        m = self._materiais(lighting)
        self.root = Object3D()
        sem_sombra = []

        # Casco em três volumes: seção central, proa cônica e popa afilada.
        corpo = Object3D()
        corpo.add(
            Mesh(
                CylinderGeometry(0.66, 0.66, 4.4, segments=32),
                m["casco"],
                position=(0.15, 0.0, 0.0),
                rotation=(0.0, 0.0, 90.0),
            ),
            Mesh(
                CylinderGeometry(0.0, 0.66, 1.35, segments=32),
                m["casco"],
                position=(3.02, 0.0, 0.0),
                rotation=(0.0, 0.0, -90.0),
            ),
            Mesh(
                CylinderGeometry(0.38, 0.66, 1.0, segments=28),
                m["casco"],
                position=(-2.55, 0.0, 0.0),
                rotation=(0.0, 0.0, 90.0),
            ),
        )
        # Faixas discretas marcam as emendas do casco.
        for x in (-1.55, -0.35, 0.85, 1.95):
            corpo.add(
                Mesh(
                    CylinderGeometry(0.673, 0.673, 0.055, segments=32),
                    m["latao"],
                    position=(x, 0.0, 0.0),
                    rotation=(0.0, 0.0, 90.0),
                )
            )
        corpo.add(
            Mesh(
                BoxGeometry(4.6, 0.16, 0.28),
                m["borracha"],
                position=(0.05, -0.60, 0.0),
            )
        )
        # Convés e chapas laterais usam a textura procedural de pintura.
        corpo.add(
            Mesh(
                BoxGeometry(3.9, 0.065, 0.82),
                m["casco_texturizado"],
                position=(0.30, 0.665, 0.0),
            )
        )
        for lado in (-1.0, 1.0):
            corpo.add(
                Mesh(
                    BoxGeometry(3.6, 0.20, 0.025),
                    m["casco_texturizado"],
                    position=(0.25, 0.26, lado * 0.655),
                )
            )
            corpo.add(
                Mesh(
                    BoxGeometry(3.2, 0.10, 0.025),
                    m["casco_texturizado"],
                    position=(0.15, -0.22, lado * 0.655),
                )
            )

        # Corrimãos finos: geometria do framework, sem participar do depth pass.
        for lado in (-1.0, 1.0):
            corpo.add(
                Mesh(
                    CylinderGeometry(0.016, 0.016, 2.55, segments=10),
                    m["metal"],
                    position=(0.55, 0.92, lado * 0.43),
                    rotation=(0.0, 0.0, 90.0),
                )
            )
            for indice in range(6):
                sem_sombra.append(
                    Mesh(
                        CylinderGeometry(0.014, 0.014, 0.27, segments=8),
                        m["metal"],
                        position=(-0.55 + indice * 0.44, 0.80, lado * 0.43),
                    )
                )
        corpo.add(*sem_sombra)

        # Torre de comando com painéis, janelas, escotilha, periscópio e antenas.
        torre = Object3D(position=(0.35, 0.0, 0.0))
        torre.add(
            Mesh(
                CylinderGeometry(0.31, 0.45, 0.62, segments=24),
                m["torre"],
                position=(0.0, 0.98, 0.0),
                scale=(1.0, 1.0, 0.72),
            ),
            Mesh(
                BoxGeometry(0.72, 0.10, 0.42),
                m["casco_texturizado"],
                position=(0.0, 1.32, 0.0),
            ),
            Mesh(
                BoxGeometry(0.02, 0.14, 0.30),
                m["janela"],
                position=(0.326, 1.10, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.17, 0.17, 0.05, segments=20),
                m["latao"],
                position=(-0.12, 1.405, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.045, 0.045, 0.86, segments=12),
                m["metal"],
                position=(0.18, 1.80, 0.0),
            ),
            Mesh(
                BoxGeometry(0.22, 0.06, 0.07),
                m["metal"],
                position=(0.25, 2.22, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.012, 0.012, 1.30, segments=8),
                m["metal"],
                position=(-0.22, 2.00, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.060, 0.060, 0.56, segments=10),
                m["metal"],
                position=(-0.38, 1.70, 0.0),
            ),
            Mesh(
                BoxGeometry(0.19, 0.06, 0.09),
                m["borracha"],
                position=(-0.38, 1.99, 0.0),
            ),
            Mesh(
                SphereGeometry(segments=16, rings=8),
                m["metal"],
                position=(0.02, 1.53, 0.0),
                scale=(0.12, 0.035, 0.12),
            ),
        )
        for lado in (-1.0, 1.0):
            torre.add(
                Mesh(
                    BoxGeometry(0.26, 0.12, 0.018),
                    m["janela"],
                    position=(-0.02, 1.13, lado * 0.238),
                )
            )
        # Holofote frontal, com lente emissiva.
        torre.add(
            Mesh(
                CylinderGeometry(0.13, 0.16, 0.22, segments=16),
                m["metal"],
                position=(0.38, 1.02, 0.0),
                rotation=(0.0, 0.0, -90.0),
            ),
            Mesh(
                CylinderGeometry(0.105, 0.105, 0.025, segments=16),
                m["holofote"],
                position=(0.50, 1.02, 0.0),
                rotation=(0.0, 0.0, -90.0),
            ),
        )

        # Vigias: aro de latão e vidro quente em ambos os lados.
        for lado in (-1.0, 1.0):
            for x in (-1.25, -0.45, 0.35, 1.15):
                corpo.add(
                    Mesh(
                        CylinderGeometry(0.095, 0.095, 0.035, segments=18),
                        m["latao"],
                        position=(x, 0.16, lado * 0.665),
                        rotation=(90.0, 0.0, 0.0),
                    ),
                    Mesh(
                        CylinderGeometry(0.066, 0.066, 0.040, segments=18),
                        m["luz_quente"],
                        position=(x, 0.16, lado * 0.682),
                        rotation=(90.0, 0.0, 0.0),
                    ),
                )

        # Luzes de navegação: bombordo vermelho, estibordo verde e popa branca.
        luzes_navegacao = (
            Mesh(
                SphereGeometry(segments=12, rings=6),
                m["luz_vermelha"],
                position=(2.18, 0.04, -0.67),
                scale=(0.07, 0.07, 0.07),
            ),
            Mesh(
                SphereGeometry(segments=12, rings=6),
                m["luz_verde"],
                position=(2.18, 0.04, 0.67),
                scale=(0.07, 0.07, 0.07),
            ),
            Mesh(
                SphereGeometry(segments=12, rings=6),
                m["luz_branca"],
                position=(-3.02, 0.36, 0.0),
                scale=(0.065, 0.065, 0.065),
            ),
        )
        sem_sombra.extend(luzes_navegacao)
        corpo.add(*luzes_navegacao)

        # Planos de mergulho e leme dão silhueta reconhecível à popa.
        leme = Object3D()
        leme.add(
            Mesh(
                BoxGeometry(0.60, 0.72, 0.085),
                m["metal"],
                position=(-2.92, 0.24, 0.0),
            ),
            Mesh(
                BoxGeometry(0.66, 0.08, 0.62),
                m["metal"],
                position=(-2.63, 0.0, 0.52),
            ),
            Mesh(
                BoxGeometry(0.66, 0.08, 0.62),
                m["metal"],
                position=(-2.63, 0.0, -0.52),
            ),
        )
        proa = Object3D()
        for lado in (-1.0, 1.0):
            proa.add(
                Mesh(
                    BoxGeometry(0.58, 0.07, 0.58),
                    m["metal"],
                    position=(1.72, 0.0, lado * 0.58),
                )
            )
        proa.add(
            Mesh(
                BoxGeometry(0.34, 0.10, 0.34),
                m["latao"],
                position=(0.0, 0.72, 0.0),
            )
        )

        # Hélice com quatro pás em pivôs próprios; o conjunto gira no eixo X.
        self.helice = Object3D(position=(-3.30, 0.0, 0.0))
        self.helice.add(
            Mesh(
                CylinderGeometry(0.18, 0.22, 0.34, segments=18),
                m["helice"],
                rotation=(0.0, 0.0, 90.0),
            )
        )
        for indice in range(4):
            braco = Object3D(rotation=(indice * 90.0, 0.0, 0.0))
            braco.add(
                Mesh(
                    BoxGeometry(0.065, 0.74, 0.17),
                    m["helice"],
                    position=(0.0, 0.43, 0.0),
                    rotation=(16.0, 0.0, 0.0),
                )
            )
            self.helice.add(braco)

        self.root.add(corpo, torre, leme, proa, self.helice)
        self._sem_sombra = tuple(sem_sombra)
        self.apply()
        return self.root

    def _atualizar_sombras(self):
        """Mantém detalhes finos e luzes fora do passe de profundidade."""
        for node in self._sem_sombra:
            node.setCastShadow(False)

    def _atualizar_luzes(self):
        """Pulsa as luzes internas e aumenta a emissão durante a abdução."""
        for material, base, extra, frequencia, fase in self._night_lights:
            pulso = 0.94 + 0.06 * math.sin(self.waterTime * frequencia + fase)
            material.emissiveStrength = base * pulso + self.glow * extra
        for material in self._glow_materials:
            material.emissiveStrength = self.glow * 0.22

    def apply(self, animationTime=None):
        """Copia o estado de animação para as transformações do modelo."""
        if animationTime is not None:
            self.waterTime = animationTime
        surface = water_height(self.position[0], self.position[2], self.waterTime)
        self.castsShadow = self.position[1] + C.SUB_TOWER_TOP * self.scale > surface
        if self.root is None:
            return

        self.root.visible = self.visible
        self.root.setCastShadow(self.castsShadow)
        self._atualizar_sombras()
        self.root.setPosition(*(float(coordenada) for coordenada in self.position))
        self.root.setRotation(
            math.degrees(self.roll),
            math.degrees(self.yaw),
            math.degrees(self.pitch),
        )
        self.root.setScale(self.scale, self.scale, self.scale)
        self._atualizar_luzes()
        if self.helice is not None:
            self.helice.setRotation(math.degrees(self.prop_angle), 0.0, 0.0)
