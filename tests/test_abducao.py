"""Teste sem OpenGL: a máquina de estados percorre o ciclo e reinicia.
Rodar: python -m tests.test_abducao
"""
from src.entities.submarino import Submarino
from src.entities.disco_voador import DiscoVoador
from src.interaction.abducao import AbducaoController, Estado


def rodar(dt, passos=20000):
    sub, disc = Submarino(), DiscoVoador()
    ctrl = AbducaoController(sub, disc)
    vistos = []
    for _ in range(passos):
        ctrl.update(dt)
        if not vistos or vistos[-1] != ctrl.estado:
            vistos.append(ctrl.estado)
        if len(vistos) > 1 and ctrl.estado is Estado.PATRULHA and Estado.FINAL in vistos:
            break
    return vistos


if __name__ == "__main__":
    a, b = rodar(1 / 30), rodar(1 / 120)   # FPS diferentes, mesma sequência
    esperado = [e for e in Estado] + [Estado.PATRULHA]
    assert a == esperado, a
    assert b == esperado, b
    print("OK: ciclo completo com 30 e 120 FPS:", [e.name for e in a])
