"""Classe-base simples para fontes de luz da cena."""


class Light:
    """Guarda cor e intensidade comuns às fontes locais de iluminação."""

    def __init__(self, color=(1.0, 1.0, 1.0), strength=1.0):
        self.color = tuple(color)
        self.strength = float(strength)
        self.shadowCamera = None
        self.shadowMaterial = None
        self.shadowRenderTarget = None