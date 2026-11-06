"""Dados de uma fonte direcional única para a cena."""
import math


class DirectionalLight:
    """Luz paralela definida pela direção em que seus raios se propagam."""

    def __init__(self, direction, ambient, diffuse):
        comprimento = math.sqrt(sum(componente * componente for componente in direction))
        if comprimento == 0.0:
            raise ValueError("A direção da luz não pode ser nula.")

        self.direction = tuple(componente / comprimento for componente in direction)
        self.ambient = tuple(ambient)
        self.diffuse = tuple(diffuse)