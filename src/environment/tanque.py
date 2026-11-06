"""Ambiente: tanque de testes com piso texturizado e paredes baixas."""
from pathlib import Path

from framework.core.mesh import Mesh
from framework.geometry.primitives import BoxGeometry, PlaneGeometry
from framework.material.basic import ColorMaterial
from framework.material.texture import TextureMaterial


TANQUE_LARGURA = 40.0
TANQUE_PROFUNDIDADE = 30.0
PAREDE_ALTURA = 2.5
PAREDE_ESPESSURA = 0.8


def build_tanque(scene, lighting):
    """Adiciona à cena um piso repetível e quatro paredes feitas de caixas."""
    caminho_textura = (
        Path(__file__).resolve().parents[2]
        / "assets"
        / "textures"
        / "concreto_teste.png"
    )

    # O UV cobre 5 por 3,75 imagens; cada imagem contém 4 por 4 ladrilhos,
    # resultando em 20 por 15 ladrilhos quadrados de 2 m sobre o piso.
    piso = Mesh(
        PlaneGeometry(TANQUE_LARGURA, TANQUE_PROFUNDIDADE, uv_repeat=(5.0, 3.75)),
        TextureMaterial(lighting, caminho_textura),
        position=(0.0, 0.005, 0.0),
    )
    material_parede = ColorMaterial(lighting, (0.27, 0.34, 0.35))

    parede_esquerda = Mesh(
        BoxGeometry(PAREDE_ESPESSURA, PAREDE_ALTURA, TANQUE_PROFUNDIDADE),
        material_parede,
        position=(-(TANQUE_LARGURA + PAREDE_ESPESSURA) / 2.0, PAREDE_ALTURA / 2.0, 0.0),
    )
    parede_direita = Mesh(
        BoxGeometry(PAREDE_ESPESSURA, PAREDE_ALTURA, TANQUE_PROFUNDIDADE),
        material_parede,
        position=((TANQUE_LARGURA + PAREDE_ESPESSURA) / 2.0, PAREDE_ALTURA / 2.0, 0.0),
    )
    parede_fundo = Mesh(
        BoxGeometry(TANQUE_LARGURA + 2.0 * PAREDE_ESPESSURA, PAREDE_ALTURA, PAREDE_ESPESSURA),
        material_parede,
        position=(0.0, PAREDE_ALTURA / 2.0, -(TANQUE_PROFUNDIDADE + PAREDE_ESPESSURA) / 2.0),
    )
    parede_frente = Mesh(
        BoxGeometry(TANQUE_LARGURA + 2.0 * PAREDE_ESPESSURA, PAREDE_ALTURA, PAREDE_ESPESSURA),
        material_parede,
        position=(0.0, PAREDE_ALTURA / 2.0, (TANQUE_PROFUNDIDADE + PAREDE_ESPESSURA) / 2.0),
    )

    scene.add(piso, parede_esquerda, parede_direita, parede_fundo, parede_frente)
    return scene
