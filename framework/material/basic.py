"""Materiais sólidos do framework local, calculados pelo shader Lambert."""
from framework.material.lambert import LambertMaterial


class ColorMaterial(LambertMaterial):
    """Material de cor uniforme submetido à iluminação direcional."""

    def __init__(
        self,
        lighting,
        color,
        alpha=1.0,
        emissive=(0.0, 0.0, 0.0),
        transparent=False,
        casts_shadow=True,
    ):
        super().__init__(
            lighting,
            color,
            alpha=alpha,
            emissive=emissive,
            transparent=transparent,
            casts_shadow=casts_shadow,
        )