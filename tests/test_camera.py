"""Testa os vetores da câmera sem criar contexto OpenGL.

Rodar: python -m tests.test_camera
"""
import math

from src.controls.camera_rig import calcular_vetores_movimento


def aproximadamente(a, b, tolerancia=1e-9):
    return all(math.isclose(x, y, abs_tol=tolerancia) for x, y in zip(a, b))


def test_yaw_zero_olha_para_menos_z():
    forward, right, up = calcular_vetores_movimento(0.0)
    assert aproximadamente(forward, (0.0, 0.0, -1.0))
    assert aproximadamente(right, (1.0, 0.0, 0.0))
    assert aproximadamente(up, (0.0, 1.0, 0.0))


def test_yaw_90_graus_olha_para_menos_x():
    forward, right, up = calcular_vetores_movimento(90.0)
    assert aproximadamente(forward, (-1.0, 0.0, 0.0))
    assert aproximadamente(right, (0.0, 0.0, -1.0))
    assert aproximadamente(up, (0.0, 1.0, 0.0))


def test_pitch_nao_tira_o_movimento_do_plano_horizontal():
    for pitch in (-80.0, -17.0, 0.0, 30.0, 80.0):
        forward, right, up = calcular_vetores_movimento(37.0, pitch)
        assert math.isclose(forward[1], 0.0, abs_tol=1e-9)
        assert math.isclose(right[1], 0.0, abs_tol=1e-9)
        assert math.isclose(up[1], 1.0, abs_tol=1e-9)


def test_360_graus_volta_ao_comeco():
    for delta in (0.0, 360.0, 720.0, -360.0):
        base = calcular_vetores_movimento(0.0)
        girado = calcular_vetores_movimento(delta)
        assert all(aproximadamente(a, b, 1e-9) for a, b in zip(base, girado))


def test_diagonal_normalizada_tem_norma_1():
    forward, right, _ = calcular_vetores_movimento(33.0)
    diagonal = (forward[0] + right[0], forward[1] + right[1], forward[2] + right[2])
    comprimento = math.sqrt(diagonal[0] ** 2 + diagonal[1] ** 2 + diagonal[2] ** 2)
    normalizada = tuple(componente / comprimento for componente in diagonal)
    assert math.isclose(
        math.sqrt(sum(componente * componente for componente in normalizada)),
        1.0,
        abs_tol=1e-9,
    )
    assert comprimento > 1.0


if __name__ == "__main__":
    test_yaw_zero_olha_para_menos_z()
    test_yaw_90_graus_olha_para_menos_x()
    test_pitch_nao_tira_o_movimento_do_plano_horizontal()
    test_360_graus_volta_ao_comeco()
    test_diagonal_normalizada_tem_norma_1()
    print("OK: vetores da câmera no plano horizontal e 360 graus conferem")
