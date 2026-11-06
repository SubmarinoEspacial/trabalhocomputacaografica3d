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


def rodar(delta_time, max_steps=30000):
    submarino, disco = Submarino(), DiscoVoador()
    controlador = AbducaoController(submarino, disco)
    estados = []
    tempo_animacao = 0.0
    detectou_acima_da_agua = False
    glow_em_abducao = False
    escalou_ate_minimo = False
    erro_superficie_maximo = 0.0

    for _ in range(max_steps):
        tempo_animacao += delta_time
        controlador.update(delta_time, tempo_animacao)
        submarino.apply(tempo_animacao)
        disco.apply()

        if not estados or estados[-1] is not controlador.estado:
            estados.append(controlador.estado)
        if controlador.estado is Estado.DETECCAO:
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
