"""Luz ambiente uniforme, independente de orientação de superfície."""
from light.light import Light


class AmbientLight(Light):
    """Contribuição ambiente que evita áreas totalmente sem iluminação."""