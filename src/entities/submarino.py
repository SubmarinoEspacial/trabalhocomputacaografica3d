"""Submarino noturno detalhado, composto apenas com geometrias do framework."""
import math
from pathlib import Path

import numpy as np
from core.mesh import Mesh
from core.object3d import Object3D
from core.texture import Texture
from geometry.primitives import BoxGeometry, CylinderGeometry, SphereGeometry
from src import config as C
from src.environment.mar import water_height
from src.environment.night_materials import VehiclePhongMaterial, VehicleTexturedPhongMaterial


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

        casco = VehiclePhongMaterial(
            lighting,
            C.SUB_COLOR_CASCO,
            specular=(0.65, 0.72, 0.80),
            shininess=38.0,
            emissive=C.LIGHT_COLOR,
            emissiveStrength=0.0,
        )
        casco_texturizado = VehicleTexturedPhongMaterial(
            lighting,
            textura_casco,
            color=C.SUB_COLOR_CASCO_TEX,
            repeatUV=(2.0, 1.0),
            specular=(0.48, 0.55, 0.62),
            shininess=30.0,
            emissive=C.LIGHT_COLOR,
            emissiveStrength=0.0,
        )
        torre = VehiclePhongMaterial(
            lighting,
            C.SUB_COLOR_TORRE,
            specular=(0.52, 0.59, 0.65),
            shininess=38.0,
            emissive=C.LIGHT_COLOR,
            emissiveStrength=0.0,
        )
        metal = VehiclePhongMaterial(
            lighting,
            C.SUB_COLOR_METAL,
            specular=(0.66, 0.71, 0.69),
            shininess=64.0,
        )
        latao = VehiclePhongMaterial(
            lighting,
            C.SUB_COLOR_LATAO,
            specular=(0.85, 0.72, 0.34),
            shininess=72.0,
        )
        borracha = VehiclePhongMaterial(
            lighting,
            C.SUB_COLOR_BORRACHA,
            specular=(0.22, 0.24, 0.23),
            shininess=16.0,
        )
        helice = VehiclePhongMaterial(
            lighting,
            C.SUB_COLOR_HELICE,
            specular=(0.95, 0.80, 0.42),
            shininess=80.0,
        )
        janela = VehiclePhongMaterial(
            lighting,
            (0.010, 0.045, 0.060),
            emissive=C.LIGHT_COLOR,
            emissiveStrength=1.5,
        )
        luz_quente = VehiclePhongMaterial(
            lighting,
            (0.08, 0.055, 0.025),
            emissive=C.LIGHT_COLOR,
            emissiveStrength=2.0,
        )
        # NAV_LIGHTS_COLORED mantém o realismo: bombordo vermelha, boreste verde.
        cor_nav_vermelha = C.NAV_BOMBORDO_COLOR if C.NAV_LIGHTS_COLORED else C.LIGHT_COLOR
        cor_nav_verde = C.NAV_BORESTE_COLOR if C.NAV_LIGHTS_COLORED else C.LIGHT_COLOR
        luz_vermelha = VehiclePhongMaterial(
            lighting,
            (0.10, 0.010, 0.006),
            emissive=cor_nav_vermelha,
            emissiveStrength=2.4,
        )
        luz_verde = VehiclePhongMaterial(
            lighting,
            (0.008, 0.09, 0.025),
            emissive=cor_nav_verde,
            emissiveStrength=2.4,
        )
        luz_branca = VehiclePhongMaterial(
            lighting,
            (0.12, 0.13, 0.14),
            emissive=C.LIGHT_COLOR,
            emissiveStrength=2.0,
        )
        holofote = VehiclePhongMaterial(
            lighting,
            (0.16, 0.15, 0.12),
            emissive=C.LIGHT_COLOR,
            emissiveStrength=2.8,
        )

        self._glow_materials = (casco, casco_texturizado, torre, metal, latao, helice)
        # Base das luzes, acréscimo durante a abdução, frequência e fase do pulso.
        self._night_lights = tuple(
            (material, base * C.LIGHT_INTENSITY, extra * C.LIGHT_INTENSITY, frequencia, fase)
            for material, base, extra, frequencia, fase in (
                (janela, 1.5, 1.2, 1.7, 0.0),
                (luz_quente, 2.0, 1.0, 2.2, 0.6),
                (luz_vermelha, 2.4, 1.4, 1.1, 0.0),
                (luz_verde, 2.4, 1.4, 1.1, math.pi),
                (luz_branca, 2.0, 1.2, 1.3, 1.2),
                (holofote, 2.8, 1.8, 0.9, 0.3),
            )
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
                CylinderGeometry(0.66, 0.66, 4.4, segments=C.ROUND_SEGMENTS),
                m["casco"],
                position=(0.15, 0.0, 0.0),
                rotation=(0.0, 0.0, 90.0),
            ),
            Mesh(
                CylinderGeometry(0.0, 0.66, 1.35, segments=C.ROUND_SEGMENTS),
                m["casco"],
                position=(3.02, 0.0, 0.0),
                rotation=(0.0, 0.0, -90.0),
            ),
            Mesh(
                CylinderGeometry(0.38, 0.66, 1.0, segments=C.ROUND_SEGMENTS),
                m["casco"],
                position=(-2.55, 0.0, 0.0),
                rotation=(0.0, 0.0, 90.0),
            ),
        )
        # Faixas discretas marcam as emendas do casco.
        if C.DETALHES_COMPLETOS:
            faixa = VehiclePhongMaterial(
                lighting,
                C.SUB_COLOR_FAIXA,
                specular=(0.30, 0.34, 0.40),
                shininess=24.0,
            )
            for x in (-1.55, -0.35, 0.85, 1.95):
                corpo.add(
                    Mesh(
                        CylinderGeometry(0.673, 0.673, 0.055, segments=C.ROUND_SEGMENTS),
                        faixa,
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
        if C.DETALHES_COMPLETOS:
            for lado in (-1.0, 1.0):
                corpo.add(
                    Mesh(
                        CylinderGeometry(0.016, 0.016, 2.55, segments=C.SMALL_SEGMENTS),
                        m["metal"],
                        position=(0.55, 0.92, lado * 0.43),
                        rotation=(0.0, 0.0, 90.0),
                    )
                )
                for indice in range(6):
                    sem_sombra.append(
                        Mesh(
                            CylinderGeometry(0.014, 0.014, 0.27, segments=C.SMALL_SEGMENTS),
                            m["metal"],
                            position=(-0.55 + indice * 0.44, 0.80, lado * 0.43),
                        )
                    )
        corpo.add(*sem_sombra)

        # Torre de comando com painéis, janelas, escotilha, periscópio e antenas.
        torre = Object3D(position=(0.35, 0.0, 0.0))
        torre.add(
            Mesh(
                CylinderGeometry(0.31, 0.45, 0.62, segments=C.ROUND_SEGMENTS),
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
                CylinderGeometry(0.17, 0.17, 0.05, segments=C.ROUND_SEGMENTS),
                m["latao"],
                position=(-0.12, 1.405, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.045, 0.045, 0.86, segments=C.SMALL_SEGMENTS),
                m["metal"],
                position=(0.18, 1.80, 0.0),
            ),
            Mesh(
                BoxGeometry(0.22, 0.06, 0.07),
                m["metal"],
                position=(0.25, 2.22, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.012, 0.012, 1.30, segments=C.SMALL_SEGMENTS),
                m["metal"],
                position=(-0.22, 2.00, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.060, 0.060, 0.56, segments=C.SMALL_SEGMENTS),
                m["metal"],
                position=(-0.38, 1.70, 0.0),
            ),
            Mesh(
                BoxGeometry(0.19, 0.06, 0.09),
                m["borracha"],
                position=(-0.38, 1.99, 0.0),
            ),
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
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
                CylinderGeometry(0.13, 0.16, 0.22, segments=C.ROUND_SEGMENTS),
                m["metal"],
                position=(0.38, 1.02, 0.0),
                rotation=(0.0, 0.0, -90.0),
            ),
            Mesh(
                CylinderGeometry(0.105, 0.105, 0.025, segments=C.ROUND_SEGMENTS),
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
                        CylinderGeometry(0.095, 0.095, 0.035, segments=C.ROUND_SEGMENTS),
                        m["latao"],
                        position=(x, 0.16, lado * 0.665),
                        rotation=(90.0, 0.0, 0.0),
                    ),
                    Mesh(
                        CylinderGeometry(0.066, 0.066, 0.040, segments=C.ROUND_SEGMENTS),
                        m["luz_quente"],
                        position=(x, 0.16, lado * 0.682),
                        rotation=(90.0, 0.0, 0.0),
                    ),
                )

        # Luzes de navegação: bombordo vermelho, estibordo verde e popa branca.
        luzes_navegacao = (
            Mesh(
                SphereGeometry(segments=C.SMALL_SEGMENTS, rings=C.SMALL_RINGS),
                m["luz_vermelha"],
                position=(2.18, 0.04, -0.67),
                scale=(0.07, 0.07, 0.07),
            ),
            Mesh(
                SphereGeometry(segments=C.SMALL_SEGMENTS, rings=C.SMALL_RINGS),
                m["luz_verde"],
                position=(2.18, 0.04, 0.67),
                scale=(0.07, 0.07, 0.07),
            ),
            Mesh(
                SphereGeometry(segments=C.SMALL_SEGMENTS, rings=C.SMALL_RINGS),
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
                CylinderGeometry(0.18, 0.22, 0.34, segments=C.ROUND_SEGMENTS),
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
        self._meshes = self._coletar_meshes()
        # Somente o casco e a base da torre formam a silhueta da sombra.
        self._silhueta = tuple(corpo.children[:3]) + (torre.children[0],)
        self.apply()
        return self.root

    def _coletar_meshes(self):
        """Percorre a hierarquia e devolve todas as malhas do modelo."""
        pilha = [self.root]
        meshes = []
        while pilha:
            no = pilha.pop()
            if isinstance(no, Mesh):
                meshes.append(no)
            pilha.extend(no.children)
        return tuple(meshes)

    def _atualizar_sombras(self):
        """Deixa no depth pass apenas a silhueta principal do submarino."""
        for node in self._meshes:
            node.castShadow = False
        for node in self._silhueta:
            node.castShadow = True

    def _atualizar_luzes(self):
        """Pulsa as luzes internas e aumenta a emissão durante a abdução."""
        for material, base, extra, frequencia, fase in self._night_lights:
            pulso = 0.94 + 0.06 * math.sin(self.waterTime * frequencia + fase)
            material.emissiveStrength = base * pulso + self.glow * extra
        for material in self._glow_materials:
            # HALO_INTENSITY controla o halo do submarino durante a abdução.
            material.emissiveStrength = self.glow * C.HALO_INTENSITY

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
