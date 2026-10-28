"""Submarino estilizado: estado de animação + modelo hierárquico."""
import numpy as np
from src import config as C


class Submarino:
    def __init__(self):
        self.root = None          # Object3D raiz (criado em build)
        self.helice = None        # pivô da hélice
        self.reset()

    def reset(self):
        self.position = np.array(C.SUB_START, dtype=float)
        self.yaw = 0.0
        self.scale = 1.0
        self.prop_angle = 0.0
        self.prop_speed = C.PROP_SPEED

    def build(self):
        """TODO: montar a hierarquia com geometrias do framework.

        root
        ├── corpo (cilindro/esfera escalada)
        ├── torre -> periscópio
        ├── pivô da hélice -> 3 ou 4 pás (caixas finas)
        └── aletas / leme
        """
        raise NotImplementedError

    def apply(self):
        """Copia o estado de animação para as transformações do modelo."""
        # self.root: posição = self.position, rotação Y = self.yaw, escala = self.scale
        # self.helice: rotação em torno do eixo = self.prop_angle
        pass
