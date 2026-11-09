"""Luz pontual leve usada pelo shader noturno do projeto.

O framework não possui PointLight; esta classe apenas descreve os parâmetros
que o `NoiteLightingContext` converte para o espaço do olho antes de desenhar.
"""
import numpy as np


class PointLight:
    """Fonte pontual com cor, intensidade e alcance em unidades do mundo."""

    def __init__(
        self,
        position,
        color,
        strength=1.0,
        range=8.0,
        enabled=True,
    ):
        self.position = np.array(position, dtype=float)
        self.color = tuple(float(component) for component in color)
        self.strength = max(0.0, float(strength))
        self.range = max(0.001, float(range))
        self.enabled = bool(enabled)

    def eye_position(self, view_matrix):
        """Converte a posição do mundo para o espaço do olho da câmera."""
        world = np.array(
            (self.position[0], self.position[1], self.position[2], 1.0),
            dtype=float,
        )
        return (view_matrix @ world)[:3]

    def eye_color(self):
        """Pré-multiplica a intensidade para simplificar o shader."""
        if not self.enabled:
            return (0.0, 0.0, 0.0)
        return tuple(component * self.strength for component in self.color)

    def eye_range(self):
        """Desliga a atenuação quando a fonte está desabilitada."""
        return self.range if self.enabled else 0.0
