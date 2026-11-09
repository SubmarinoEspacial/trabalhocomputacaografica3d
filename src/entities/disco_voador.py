"""Disco voador noturno detalhado, com anel de luzes e feixe volumétrico."""
import math
from pathlib import Path

import numpy as np
from core.mesh import Mesh
from core.object3d import Object3D
from core.texture import Texture
from geometry.primitives import BoxGeometry, ConeGeometry, CylinderGeometry, SphereGeometry
from material.phong import PhongMaterial
from src import config as C
from src.environment.effects import BeamMaterial
from src.environment.night_materials import TexturedPhongMaterial


class DiscoVoador:
    def __init__(self):
        self.root = None
        self.anel = None          # pivô do anel de luzes (gira)
        self.feixe = None         # grupo do feixe (filho do disco)
        self._light_materials = ()
        self._beam_materials = ()
        self._sem_sombra = ()
        self.reset()

    def reset(self):
        self.position = np.array(C.DISC_START, dtype=float)
        self.yaw = 0.0
        self.hover_phase = 0.0
        self.ring_angle = 0.0
        self.beam_amount = 0.0    # 0 = desligado, 1 = totalmente ligado
        if self.root is not None:
            self.root.visible = True

    @property
    def hover_offset(self):
        return C.DISC_HOVER_AMP * math.sin(self.hover_phase)

    def _materiais(self, lighting):
        """Cria os materiais metálicos, vidro da cúpula e luzes do disco."""
        raiz = Path(__file__).resolve().parents[2]
        textura_paineis = Texture(
            raiz / "assets" / "textures" / "paineis_disco_procedural.png"
        )
        textura_feixe = Texture(
            raiz / "assets" / "textures" / "feixe_ruido_procedural.png"
        )
        self._panelTexture = textura_paineis
        self._beamTexture = textura_feixe

        casco = PhongMaterial(
            lighting,
            (0.17, 0.22, 0.25),
            specular=(0.72, 0.80, 0.84),
            shininess=88.0,
        )
        casco_escuro = PhongMaterial(
            lighting,
            (0.065, 0.085, 0.10),
            specular=(0.34, 0.38, 0.40),
            shininess=52.0,
        )
        painel = TexturedPhongMaterial(
            lighting,
            textura_paineis,
            color=(0.84, 0.92, 0.98),
            repeatUV=(1.5, 1.0),
            specular=(0.48, 0.55, 0.58),
            shininess=60.0,
        )
        metal = PhongMaterial(
            lighting,
            (0.44, 0.47, 0.45),
            specular=(0.86, 0.90, 0.88),
            shininess=110.0,
        )
        latao = PhongMaterial(
            lighting,
            (0.42, 0.34, 0.14),
            specular=(0.90, 0.72, 0.34),
            shininess=100.0,
        )
        aro_luz = PhongMaterial(
            lighting,
            (0.02, 0.09, 0.13),
            emissive=(0.06, 0.42, 0.72),
            emissiveStrength=0.55,
        )
        domo = PhongMaterial(
            lighting,
            (0.035, 0.16, 0.21),
            specular=(0.90, 0.96, 1.0),
            shininess=140.0,
            alpha=0.62,
            emissive=(0.03, 0.22, 0.34),
            emissiveStrength=0.45,
            transparent=True,
            casts_shadow=False,
        )
        cockpit = PhongMaterial(
            lighting,
            (0.03, 0.17, 0.23),
            emissive=(0.12, 0.68, 0.92),
            emissiveStrength=1.35,
        )

        luzes = []
        for color in C.DISC_LIGHT_COLORS:
            luzes.append(
                PhongMaterial(
                    lighting,
                    tuple(componente * 0.16 for componente in color),
                    emissive=color,
                    emissiveStrength=2.0,
                )
            )
        self._light_materials = tuple(
            (material, 2.0, indice * 1.37)
            for indice, material in enumerate(luzes)
        )

        self._beam_materials = (
            BeamMaterial(
                textura_feixe,
                color=C.BEAM_COLOR,
                intensity=0.0,
                height=2.5,
                radius_bottom=1.35,
                radius_top=0.02,
            ),
            BeamMaterial(
                textura_feixe,
                color=C.BEAM_CORE_COLOR,
                intensity=0.0,
                height=2.46,
                radius_bottom=0.52,
                radius_top=0.015,
            ),
        )
        return {
            "casco": casco,
            "casco_escuro": casco_escuro,
            "painel": painel,
            "metal": metal,
            "latao": latao,
            "aro_luz": aro_luz,
            "domo": domo,
            "cockpit": cockpit,
            "luzes": luzes,
        }

    def build(self, lighting):
        """Monta casco em camadas, cúpula, anéis luminosos e feixe cônico."""
        if self.root is not None:
            return self.root

        m = self._materiais(lighting)
        self.root = Object3D()
        sem_sombra = []

        corpo = Object3D()
        corpo.add(
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
                m["casco"],
                position=(0.0, -0.08, 0.0),
                scale=(1.80, 0.22, 1.42),
            ),
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
                m["casco"],
                position=(0.0, 0.10, 0.0),
                scale=(1.66, 0.26, 1.30),
            ),
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
                m["metal"],
                position=(0.0, 0.02, 0.0),
                scale=(1.94, 0.10, 1.54),
            ),
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
                m["casco_escuro"],
                position=(0.0, -0.28, 0.0),
                scale=(1.12, 0.24, 0.92),
            ),
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
                m["aro_luz"],
                position=(0.0, 0.04, 0.0),
                scale=(1.90, 0.045, 1.52),
            ),
        )

        # Painéis superiores com UV de caixa, distribuídos em anel.
        if C.DETALHES_COMPLETOS:
            for indice in range(12):
                angulo = 2.0 * math.pi * indice / 12.0
                corpo.add(
                    Mesh(
                        BoxGeometry(0.42, 0.032, 0.24),
                        m["painel"],
                        position=(1.40 * math.cos(angulo), 0.205, 1.10 * math.sin(angulo)),
                        rotation=(0.0, math.degrees(angulo) + 90.0, 0.0),
                    )
                )

        # Base da cúpula, vidro e cabine interna iluminada.
        corpo.add(
            Mesh(
                CylinderGeometry(0.62, 0.72, 0.14, segments=C.ROUND_SEGMENTS),
                m["latao"],
                position=(0.0, 0.285, 0.0),
            ),
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
                m["cockpit"],
                position=(0.0, 0.40, 0.0),
                scale=(0.30, 0.22, 0.30),
            ),
            Mesh(
                SphereGeometry(segments=C.ROUND_SEGMENTS, rings=C.ROUND_RINGS),
                m["domo"],
                position=(0.0, 0.42, 0.0),
                scale=(0.60, 0.46, 0.60),
            ),
        )
        sem_sombra.append(corpo.children[-1])

        # Antena curta no topo da cúpula.
        corpo.add(
            Mesh(
                CylinderGeometry(0.012, 0.012, 0.44, segments=C.SMALL_SEGMENTS),
                m["metal"],
                position=(0.0, 0.93, 0.0),
            ),
            Mesh(
                SphereGeometry(segments=C.SMALL_SEGMENTS, rings=C.SMALL_RINGS),
                m["aro_luz"],
                position=(0.0, 1.16, 0.0),
                scale=(0.045, 0.045, 0.045),
            ),
        )

        # Emissor inferior e quatro luzes auxiliares.
        corpo.add(
            Mesh(
                CylinderGeometry(0.34, 0.48, 0.15, segments=C.ROUND_SEGMENTS),
                m["latao"],
                position=(0.0, -0.42, 0.0),
            ),
            Mesh(
                CylinderGeometry(0.22, 0.22, 0.035, segments=C.ROUND_SEGMENTS),
                m["aro_luz"],
                position=(0.0, -0.50, 0.0),
            ),
        )
        for indice in range(8):
            angulo = 2.0 * math.pi * indice / 8.0
            luz = Mesh(
                SphereGeometry(segments=C.SMALL_SEGMENTS, rings=C.SMALL_RINGS),
                m["luzes"][indice % len(m["luzes"])],
                position=(0.92 * math.cos(angulo), -0.27, 0.92 * math.sin(angulo)),
                scale=(0.065, 0.065, 0.065),
            )
            sem_sombra.append(luz)
            corpo.add(luz)

        # Anel externo com luzes alternadas; a quantidade vem do perfil de qualidade.
        self.anel = Object3D(position=(0.0, 0.04, 0.0))
        for indice in range(C.DISC_RING_LIGHTS):
            angulo = 2.0 * math.pi * indice / C.DISC_RING_LIGHTS
            raio = 1.83
            luz = Mesh(
                SphereGeometry(segments=C.SMALL_SEGMENTS, rings=C.SMALL_RINGS),
                m["luzes"][indice % len(m["luzes"])],
                position=(raio * math.cos(angulo), 0.0, raio * math.sin(angulo)),
                scale=(0.105, 0.105, 0.105),
            )
            sem_sombra.append(luz)
            self.anel.add(luz)

        # Feixe: cone externo suave e núcleo mais estreito, ambos aditivos.
        self.feixe = Object3D(position=(0.0, -1.28, 0.0))
        feixe_externo = Mesh(
            ConeGeometry(radius=1.12, height=2.50, segments=C.ROUND_SEGMENTS),
            self._beam_materials[0],
        )
        feixe_core = Mesh(
            ConeGeometry(radius=0.42, height=2.46, segments=C.ROUND_SEGMENTS),
            self._beam_materials[1],
            position=(0.0, 0.02, 0.0),
        )
        self.feixe.add(feixe_externo, feixe_core)
        sem_sombra.extend((feixe_externo, feixe_core))

        self.root.add(corpo, self.anel, self.feixe)
        self._sem_sombra = tuple(sem_sombra)
        self._meshes = self._coletar_meshes()
        # Somente as quatro camadas principais do disco formam a silhueta da sombra.
        self._silhueta = tuple(corpo.children[:4])
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
        """Deixa no depth pass apenas a silhueta principal do disco."""
        for node in self._meshes:
            node.castShadow = False
        for node in self._silhueta:
            node.castShadow = True

    def apply(self):
        """Aplica flutuação, rotação do anel, luzes e estado do feixe."""
        if self.root is None:
            return

        self.root.setPosition(
            float(self.position[0]),
            float(self.position[1] + self.hover_offset),
            float(self.position[2]),
        )
        self.root.setRotation(0.0, math.degrees(self.yaw), 0.0)
        self.root.setScale(C.DISC_SCALE, C.DISC_SCALE, C.DISC_SCALE)
        self._atualizar_sombras()
        if self.anel is not None:
            self.anel.setRotation(0.0, math.degrees(self.ring_angle), 0.0)

        tempo = self.hover_phase / max(C.DISC_HOVER_FREQ, 1e-6)
        for material, base, fase in self._light_materials:
            pulso = 0.90 + 0.10 * math.sin(tempo * 2.4 + fase)
            material.emissiveStrength = base * pulso + self.beam_amount * 0.35

        if self.feixe is not None:
            amount = max(0.0, min(1.0, float(self.beam_amount)))
            self.feixe.visible = amount > 0.002
            self.feixe.setScale(amount, amount, amount)
            externo, core = self._beam_materials
            externo.time = tempo
            core.time = tempo
            externo.set_amount(C.BEAM_OUTER_ALPHA * amount)
            core.set_amount(C.BEAM_CORE_ALPHA * amount)
