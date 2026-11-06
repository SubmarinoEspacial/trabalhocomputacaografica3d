"""Material especular Phong usando o shader de superfície compartilhado."""
from material.lambert import LambertMaterial


class PhongMaterial(LambertMaterial):
    """Material com componente especular avaliada por fragmento."""

    def __init__(
        self,
        lighting,
        color,
        specular=(0.35, 0.35, 0.35),
        shininess=40.0,
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
            specular=specular,
            shininess=shininess,
            transparent=transparent,
            casts_shadow=casts_shadow,
        )