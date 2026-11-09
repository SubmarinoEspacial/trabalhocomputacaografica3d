"""Ambiente de mar aberto: fundo de areia e superfície transparente."""
from pathlib import Path
import math

from core.mesh import Mesh
from core.texture import Texture
from geometry.primitives import PlaneGeometry, WaterGridGeometry
from material.texture import TextureMaterial
from src import config as C
from src.environment.night_materials import NoiteWaterMaterial


def water_height(x, z, t):
    """Altura absoluta da superfície, usando a mesma soma do shader de vértice."""
    height = C.WATER_LEVEL
    ondas = C.WATER_WAVES + C.WATER_DETAIL_WAVES
    for direction_x, direction_z, amplitude, wave_number, speed in ondas:
        phase = wave_number * (direction_x * x + direction_z * z) + speed * t
        height += amplitude * math.sin(phase)
    return height


def water_slope(x, z, t):
    """Retorna dH/dx e dH/dz para inclinar o submarino sobre a onda."""
    derivative_x = 0.0
    derivative_z = 0.0
    ondas = C.WATER_WAVES + C.WATER_DETAIL_WAVES
    for direction_x, direction_z, amplitude, wave_number, speed in ondas:
        phase = wave_number * (direction_x * x + direction_z * z) + speed * t
        slope = amplitude * wave_number * math.cos(phase)
        derivative_x += slope * direction_x
        derivative_z += slope * direction_z
    return derivative_x, derivative_z


def build_mar(scene, lighting) -> NoiteWaterMaterial:
    """Adiciona o fundo marinho e a grade de água à cena e retorna o material."""
    caminho_areia = (
        Path(__file__).resolve().parents[2]
        / "assets"
        / "textures"
        / "areia_beach_sandy_shore_cc0.jpg"
    )
    fundo = Mesh(
        PlaneGeometry(C.WATER_WIDTH, C.WATER_DEPTH),
        TextureMaterial(
            lighting,
            Texture(caminho_areia),
            repeatUV=(16.0, 13.0),
        ),
        position=(0.0, C.WATER_LEVEL - C.SEA_FLOOR_DEPTH, 0.0),
    )
    fundo.setReceiveShadow(True)

    material_agua = NoiteWaterMaterial(lighting)
    agua = Mesh(
        WaterGridGeometry(
            C.WATER_WIDTH,
            C.WATER_DEPTH,
            segments=C.WATER_GRID_RESOLUTION,
        ),
        material_agua,
        position=(0.0, C.WATER_LEVEL, 0.0),
    )
    agua.setCastShadow(False)
    agua.setReceiveShadow(True)
    scene.add(fundo, agua)
    return material_agua