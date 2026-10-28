"""Disco voador: estado de animação + modelo hierárquico."""
import math
import numpy as np
from src import config as C


class DiscoVoador:
    def __init__(self):
        self.root = None
        self.anel = None          # pivô do anel de luzes (gira)
        self.feixe = None         # cone/cilindro do feixe (filho do disco)
        self.reset()

    def reset(self):
        self.position = np.array(C.DISC_START, dtype=float)
        self.hover_phase = 0.0
        self.ring_angle = 0.0
        self.beam_amount = 0.0    # 0 = desligado, 1 = totalmente ligado

    @property
    def hover_offset(self):
        return C.DISC_HOVER_AMP * math.sin(self.hover_phase)

    def build(self):
        """TODO: montar a hierarquia com geometrias do framework.

        root
        ├── corpo (esfera achatada: escala Y pequena)
        ├── cúpula (esfera menor)
        ├── anel (pivô que gira) -> esferas pequenas (luzes)
        └── feixe (cone de base maior; escala em Y = beam_amount)
        """
        raise NotImplementedError

    def apply(self):
        # posição final = self.position + (0, self.hover_offset, 0)
        # self.anel: rotação em Y = self.ring_angle
        # self.feixe: visível se beam_amount > 0, escala = beam_amount
        pass
