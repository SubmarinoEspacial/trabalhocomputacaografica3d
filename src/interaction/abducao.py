"""Máquina de estados da abdução (lógica pura, sem OpenGL).

Todos os movimentos usam delta time (dt) em segundos, então a velocidade
não depende da taxa de quadros. Com dt = 0 a animação fica pausada.
"""
import math
from enum import Enum, auto
import numpy as np
from src import config as C
from src.environment.mar import water_height, water_slope


class Estado(Enum):
    SUBMERSO = auto()
    EMERGINDO = auto()
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
        self.estado = Estado.SUBMERSO
        self.t_estado = 0.0
        self.t_total = 0.0
        self.angulo = 0.0
        self._y0 = 0.0
        self._emergence_start_y = C.SUB_START[1]
        self._emergence_elapsed = 0.0
        self._emergence_complete = False
        self.sub.reset()
        self.disc.reset()

    def _ir_para(self, novo):
        self.estado = novo
        self.t_estado = 0.0

    def update(self, dt, animation_time=None):
        if dt <= 0:
            return
        self.t_total += dt
        self.t_estado += dt
        sub, disc = self.sub, self.disc
        tempo_animacao = self.t_total if animation_time is None else animation_time
        sub.waterTime = tempo_animacao

        sub.waterTime = tempo_animacao
        disc.hover_phase = tempo_animacao * C.DISC_HOVER_FREQ
        disc.ring_angle += C.RING_SPEED * dt
        sub.prop_angle += sub.prop_speed * dt

        e = self.estado
        if e is Estado.SUBMERSO:
            sub.prop_speed = C.PROP_SPEED
            sub.position[0] += C.SUB_SPEED * dt
            if self.t_estado >= C.SUBMERGED_TIME:
                self._emergence_start_y = float(sub.position[1])
                self._emergence_elapsed = 0.0
                self._emergence_complete = False
                self._ir_para(Estado.EMERGINDO)

        elif e is Estado.EMERGINDO:
            sub.prop_speed = C.PROP_SPEED
            sub.position[0] += C.SUB_SPEED * dt
            self._update_surface(dt, tempo_animacao)
            topo_torre = sub.position[1] + C.SUB_TOWER_TOP * sub.scale
            distancia = np.linalg.norm(_horizontal(disc.position - sub.position))
            if topo_torre > water_height(sub.position[0], sub.position[2], tempo_animacao) and distancia < C.DETECT_RADIUS:
                self._ir_para(Estado.DETECCAO)

        elif e is Estado.DETECCAO:
            # O submarino ajusta o percurso: gira o nariz em yaw na direção do
            # disco e avança até o ponto da superfície logo abaixo dele, parando
            # ali com a hélice desacelerando; o disco, ao mesmo tempo, se aproxima
            # e se posiciona acima. Só depois disso segue para POSICIONAMENTO.
            self._update_surface(dt, tempo_animacao)
            self._girar_sub_para_disco(dt)
            self._mover_sub_para_abaixo_do_disco(dt)
            self._girar_disco_para_sub()
            self._mover_disco_para_cima_do_sub(dt)
            alvo = self._alvo_acima_do_sub()
            distancia_sub = np.linalg.norm(_horizontal(disc.position - sub.position))
            if (
                distancia_sub <= C.ARRIVE_EPS
                and np.linalg.norm(alvo - disc.position) <= C.DETECTION_APPROACH_RADIUS
            ):
                self._ir_para(Estado.POSICIONAMENTO)

        elif e is Estado.POSICIONAMENTO:
            self._update_surface(dt, tempo_animacao)
            sub.prop_speed = max(0.0, sub.prop_speed - 8.0 * dt)
            self._girar_disco_para_sub()
            self._mover_disco_para_cima_do_sub(dt)
            alvo = self._alvo_acima_do_sub()
            if sub.prop_speed <= 0.01 and np.linalg.norm(alvo - disc.position) < C.ARRIVE_EPS:
                self.angulo = 0.0
                self._ir_para(Estado.INSPECAO)

        elif e is Estado.INSPECAO:
            self._update_surface(dt, tempo_animacao)
            self.angulo += C.ORBIT_OMEGA * dt
            centro = sub.position + np.array([0.0, C.DISC_HEIGHT_OVER_SUB, 0.0])
            disc.position[:] = centro + C.ORBIT_RADIUS * np.array(
                [math.cos(self.angulo), 0.0, math.sin(self.angulo)])
            if self.angulo >= 2 * math.pi:
                self._ir_para(Estado.FEIXE)

        elif e is Estado.FEIXE:
            self._update_surface(dt, tempo_animacao)
            self._mover_disco_para_cima_do_sub(dt)
            disc.beam_amount = smoothstep(self.t_estado / C.BEAM_TIME)
            sub.glow = smoothstep(self.t_estado / C.GLOW_RISE_TIME)
            if self.t_estado >= C.BEAM_TIME:
                self._y0 = sub.position[1]
                self._ir_para(Estado.ABDUCAO)

        elif e is Estado.ABDUCAO:
            k = smoothstep(self.t_estado / C.ABDUCT_TIME)
            sub.position[1] = self._y0 + C.ABDUCT_RISE * k
            sub.pitch = 0.0
            sub.roll = 0.0
            sub.yaw += C.ABDUCT_SPIN * dt
            sub.scale = 1.0 - (1.0 - C.ABDUCT_MIN_SCALE) * k
            pulso = 0.84 + C.GLOW_PULSE_AMPLITUDE * math.sin(
                tempo_animacao * C.GLOW_PULSE_FREQUENCY
            )
            sub.glow = max(0.0, min(1.0, pulso))
            if self.t_estado >= C.ABDUCT_TIME:
                sub.visible = False
                sub.castsShadow = False
                self._ir_para(Estado.FINAL)

        elif e is Estado.FINAL:
            disc.beam_amount = max(0.0, disc.beam_amount - dt)
            sub.glow = max(0.0, sub.glow - C.GLOW_FADE_SPEED * dt)
            if self.t_estado >= C.FINAL_WAIT:
                self.reset()  # reinicia o loop da demonstração

    def _update_surface(self, dt, animation_time):
        """Segue a altura analítica e deriva atitude do plano tangente da onda."""
        sub = self.sub
        surface = water_height(sub.position[0], sub.position[2], animation_time)
        if not self._emergence_complete:
            self._emergence_elapsed = min(
                C.EMERGE_TIME,
                self._emergence_elapsed + dt,
            )
            progress = smoothstep(self._emergence_elapsed / C.EMERGE_TIME)
            target_y = surface + C.SUB_SURFACE_OFFSET
            sub.position[1] = self._emergence_start_y + (target_y - self._emergence_start_y) * progress
            if self._emergence_elapsed >= C.EMERGE_TIME:
                self._emergence_complete = True
        else:
            progress = 1.0
            sub.position[1] = surface + C.SUB_SURFACE_OFFSET

        slope_x, slope_z = water_slope(sub.position[0], sub.position[2], animation_time)
        emergence_tilt = math.radians(C.EMERGE_PITCH) * (1.0 - progress)
        sub.pitch = math.atan(slope_x) + emergence_tilt
        sub.roll = -math.atan(slope_z) * C.SURFACE_ROLL_FACTOR

    def _girar_disco_para_sub(self):
        delta = self.sub.position - self.disc.position
        self.disc.yaw = math.atan2(delta[0], -delta[2])

    def _girar_sub_para_disco(self, dt):
        """Giro suave do yaw na direção horizontal do disco (interpolação por dt)."""
        delta = _horizontal(self.disc.position - self.sub.position)
        distancia = np.linalg.norm(delta)
        if distancia < C.ARRIVE_EPS:
            # Já está abaixo do disco; evita girar sobre um alvo quase nulo.
            return
        # Com yaw = 0 o nariz do submarino aponta para +X (rotação sobre Y).
        alvo = math.atan2(-delta[2], delta[0])
        diferenca = (alvo - self.sub.yaw + math.pi) % (2.0 * math.pi) - math.pi
        passo_maximo = math.radians(C.SUB_TURN_SPEED) * dt
        self.sub.yaw += max(-passo_maximo, min(passo_maximo, diferenca))

    def _mover_sub_para_abaixo_do_disco(self, dt):
        """Avança até o ponto da superfície logo abaixo do disco e para ali."""
        sub = self.sub
        delta = _horizontal(self.disc.position - sub.position)
        distancia = np.linalg.norm(delta)
        if distancia <= C.ARRIVE_EPS:
            # Chegou: a hélice desacelera até parar (mesma taxa do POSICIONAMENTO).
            sub.prop_speed = max(0.0, sub.prop_speed - 8.0 * dt)
            return
        fracao = min(1.0, distancia / 2.0)    # desacelera nos últimos 2 m
        velocidade = C.SUB_APPROACH_SPEED * fracao
        passo = min(distancia, velocidade * dt)
        direcao = delta / distancia
        sub.position[0] += direcao[0] * passo
        sub.position[2] += direcao[2] * passo
        sub.prop_speed = C.PROP_SPEED * fracao

    def _alvo_acima_do_sub(self):
        return self.sub.position + np.array([0.0, C.DISC_HEIGHT_OVER_SUB, 0.0])

    def _mover_disco_para_cima_do_sub(self, dt):
        alvo = self._alvo_acima_do_sub()
        d = alvo - self.disc.position
        dist = np.linalg.norm(d)
        if dist > 1e-6:
            passo = min(dist, C.DISC_SPEED * dt)
            self.disc.position += d / dist * passo
