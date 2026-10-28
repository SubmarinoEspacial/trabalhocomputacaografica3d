"""Máquina de estados da abdução (lógica pura, sem OpenGL).

Todos os movimentos usam delta time (dt) em segundos, então a velocidade
não depende da taxa de quadros. Com dt = 0 a animação fica pausada.
"""
import math
from enum import Enum, auto
import numpy as np
from src import config as C


class Estado(Enum):
    PATRULHA = auto()
    DETECCAO = auto()
    POSICIONAMENTO = auto()
    INSPECAO = auto()
    FEIXE = auto()
    ABDUCAO = auto()
    FINAL = auto()


def smoothstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _horizontal(v):
    return np.array([v[0], 0.0, v[2]])


class AbducaoController:
    def __init__(self, sub, disc):
        self.sub, self.disc = sub, disc
        self.reset()

    def reset(self):
        self.estado = Estado.PATRULHA
        self.t_estado = 0.0
        self.t_total = 0.0
        self.angulo = 0.0
        self._y0 = 0.0
        self.sub.reset()
        self.disc.reset()

    def _ir_para(self, novo):
        self.estado = novo
        self.t_estado = 0.0

    def update(self, dt):
        if dt <= 0:
            return
        self.t_total += dt
        self.t_estado += dt
        sub, disc = self.sub, self.disc

        # disco sempre flutua e o anel sempre gira
        disc.hover_phase = self.t_total * C.DISC_HOVER_FREQ
        disc.ring_angle += C.RING_SPEED * dt
        sub.prop_angle += sub.prop_speed * dt

        e = self.estado
        if e is Estado.PATRULHA:
            sub.prop_speed = C.PROP_SPEED
            sub.position[0] += C.SUB_SPEED * dt
            if np.linalg.norm(_horizontal(disc.position - sub.position)) < C.DETECT_RADIUS:
                self._ir_para(Estado.DETECCAO)

        elif e is Estado.DETECCAO:
            sub.prop_speed = C.PROP_SPEED * 2
            sub.position[0] += C.SUB_SPEED_FLEE * dt
            self._mover_disco_para_cima_do_sub(dt)
            if self.t_estado >= C.FLEE_TIME:
                self._ir_para(Estado.POSICIONAMENTO)

        elif e is Estado.POSICIONAMENTO:
            sub.prop_speed = max(0.0, sub.prop_speed - 8.0 * dt)
            self._mover_disco_para_cima_do_sub(dt)
            alvo = self._alvo_acima_do_sub()
            if sub.prop_speed <= 0.01 and np.linalg.norm(_horizontal(alvo - disc.position)) < C.ARRIVE_EPS:
                self.angulo = 0.0
                self._ir_para(Estado.INSPECAO)

        elif e is Estado.INSPECAO:
            self.angulo += C.ORBIT_OMEGA * dt
            centro = sub.position + np.array([0.0, C.DISC_HEIGHT_OVER_SUB, 0.0])
            disc.position[:] = centro + C.ORBIT_RADIUS * np.array(
                [math.cos(self.angulo), 0.0, math.sin(self.angulo)])
            if self.angulo >= 2 * math.pi:
                self._ir_para(Estado.FEIXE)

        elif e is Estado.FEIXE:
            self._mover_disco_para_cima_do_sub(dt)
            disc.beam_amount = smoothstep(self.t_estado / C.BEAM_TIME)
            if self.t_estado >= C.BEAM_TIME:
                self._y0 = sub.position[1]
                self._ir_para(Estado.ABDUCAO)

        elif e is Estado.ABDUCAO:
            k = smoothstep(self.t_estado / C.ABDUCT_TIME)
            sub.position[1] = self._y0 + C.ABDUCT_RISE * k
            sub.yaw += C.ABDUCT_SPIN * dt
            sub.scale = 1.0 - (1.0 - C.ABDUCT_MIN_SCALE) * k
            if self.t_estado >= C.ABDUCT_TIME:
                self._ir_para(Estado.FINAL)

        elif e is Estado.FINAL:
            disc.beam_amount = max(0.0, disc.beam_amount - dt)
            if self.t_estado >= C.FINAL_WAIT:
                self.reset()  # reinicia o loop da demonstração

    def _alvo_acima_do_sub(self):
        return self.sub.position + np.array([0.0, C.DISC_HEIGHT_OVER_SUB, 0.0])

    def _mover_disco_para_cima_do_sub(self, dt):
        alvo = self._alvo_acima_do_sub()
        d = alvo - self.disc.position
        dist = np.linalg.norm(d)
        if dist > 1e-6:
            passo = min(dist, C.DISC_SPEED * dt)
            self.disc.position += d / dist * passo
