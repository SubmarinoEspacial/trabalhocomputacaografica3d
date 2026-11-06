"""Materiais sólidos do framework local, calculados pelo shader Lambert."""
from framework.material.lambert import LambertMaterial


class ColorMaterial(LambertMaterial):
    """Material de cor uniforme submetido à iluminação direcional."""

    def __init__(self, lighting, color):
        super().__init__(lighting, color)