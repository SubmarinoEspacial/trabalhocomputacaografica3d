"""Testa o ciclo marinho sem criar contexto OpenGL.

Rodar: python -m tests.test_abducao
"""
import math

from src import config as C
from src.entities.disco_voador import DiscoVoador
from src.entities.submarino import Submarino
from src.environment.mar import water_height
from src.interaction.abducao import AbducaoController, Estado


SEQUENCIA_ESPERADA = [
    Estado.SUBMERSO,
    Estado.EMERGINDO,
    Estado.DETECCAO,
    Estado.POSICIONAMENTO,
    Estado.INSPECAO,
    Estado.FEIXE,
    Estado.ABDUCAO,
    Estado.FINAL,
    Estado.SUBMERSO,
]


def distancia_horizontal(a, b):
    return math.hypot(float(a[0] - b[0]), float(a[2] - b[2]))


def rodar(delta_time, max_steps=30000):
    submarino, disco = Submarino(), DiscoVoador()
    controlador = AbducaoController(submarino, disco)
    estados = []
    tempo_animacao = 0.0
    detectou_acima_da_agua = False
    glow_em_abducao = False
    escalou_ate_minimo = False
    erro_superficie_maximo = 0.0
    posicao_deteccao = None            # onde o submarino estava ao entrar em DETECCAO
    percurso_aproximacao = 0.0         # deslocamento horizontal do submarino em DETECCAO
    erro_yaw_minimo = math.inf         # menor erro angular em DETECCAO (rad)
    distancia_ao_posicionar = math.inf # distância horizontal sub→disco ao entrar em POSICIONAMENTO
    helice_parada_em_inspecao = False  # prop_speed ao entrar em INSPECAO

    for _ in range(max_steps):
        tempo_animacao += delta_time
        controlador.update(delta_time, tempo_animacao)
        submarino.apply(tempo_animacao)
        disco.apply()

        if not estados or estados[-1] is not controlador.estado:
            estados.append(controlador.estado)
            if controlador.estado is Estado.DETECCAO:
                posicao_deteccao = (float(submarino.position[0]), float(submarino.position[2]))
                erro_yaw_minimo = math.inf
            if controlador.estado is Estado.POSICIONAMENTO:
                distancia_ao_posicionar = distancia_horizontal(submarino.position, disco.position)
            if controlador.estado is Estado.INSPECAO:
                helice_parada_em_inspecao = submarino.prop_speed <= 0.01
        if controlador.estado is Estado.DETECCAO:
            if posicao_deteccao is not None:
                percurso_aproximacao = max(
                    percurso_aproximacao,
                    math.hypot(
                        float(submarino.position[0]) - posicao_deteccao[0],
                        float(submarino.position[2]) - posicao_deteccao[1],
                    ),
                )
            distancia_hd = distancia_horizontal(disco.position, submarino.position)
            if distancia_hd > 0.5:
                alvo_yaw = math.atan2(
                    -float(disco.position[2] - submarino.position[2]),
                    float(disco.position[0] - submarino.position[0]),
                )
                erro_yaw = abs((alvo_yaw - submarino.yaw + math.pi) % (2.0 * math.pi) - math.pi)
                erro_yaw_minimo = min(erro_yaw_minimo, erro_yaw)
            topo_torre = submarino.position[1] + C.SUB_TOWER_TOP * submarino.scale
            superficie = water_height(
                submarino.position[0],
                submarino.position[2],
                tempo_animacao,
            )
            detectou_acima_da_agua |= topo_torre > superficie
        if controlador.estado in (
            Estado.DETECCAO,
            Estado.POSICIONAMENTO,
            Estado.INSPECAO,
            Estado.FEIXE,
        ) and controlador._emergence_complete:
            superficie_submarino = water_height(
                submarino.position[0],
                submarino.position[2],
                tempo_animacao,
            ) + C.SUB_SURFACE_OFFSET
            erro_superficie_maximo = max(
                erro_superficie_maximo,
                abs(float(submarino.position[1]) - superficie_submarino),
            )
        if controlador.estado in (Estado.ABDUCAO, Estado.FINAL):
            glow_em_abducao |= submarino.glow > 0.0
            escalou_ate_minimo |= submarino.scale <= C.ABDUCT_MIN_SCALE + 1e-6
        if (
            controlador.estado is Estado.SUBMERSO
            and len(estados) > 1
            and Estado.FINAL in estados
            and controlador.t_total == 0.0
        ):
            break

    assert estados == SEQUENCIA_ESPERADA, [estado.name for estado in estados]
    assert detectou_acima_da_agua
    assert erro_superficie_maximo < 0.5, erro_superficie_maximo
    assert percurso_aproximacao > 4.0, percurso_aproximacao
    assert erro_yaw_minimo < 0.2, erro_yaw_minimo
    assert distancia_ao_posicionar <= C.ARRIVE_EPS + 0.05, distancia_ao_posicionar
    assert helice_parada_em_inspecao
    assert glow_em_abducao
    assert escalou_ate_minimo
    assert submarino.visible
    assert submarino.glow == 0.0
    assert disco.beam_amount == 0.0
    assert math.isclose(submarino.position[1], C.SUB_START[1])
    return estados


if __name__ == "__main__":
    estados_30 = rodar(1.0 / 30.0)
    estados_120 = rodar(1.0 / 120.0)
    assert estados_30 == estados_120
    print("OK: ciclo marinho a 30 e 120 FPS:", [estado.name for estado in estados_30])
