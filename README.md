# Trabalho Prático de Computação Gráfica (UNIPAC, 2026/02)

## Integrantes e temas
- Integrante 1: ___ (tema: ___)
- Integrante 2: ___ (tema: ___)
(Submarino Estilizado e Disco Voador)

## Descrição da cena e da interação
Tanque de testes fictício. O disco voador detecta o submarino, se posiciona,
o inspeciona em órbita, liga um feixe e o abduz. Ao final, a cena reinicia.
Sequência: Patrulha, Detecção, Posicionamento, Inspeção, Feixe, Abdução, Final.

## Instalação e execução
```
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python main.py
```
Teste da máquina de estados (sem OpenGL): `python -m tests.test_abducao`

## Controles
W/A/S/D mover, Q/E subir/descer, setas girar, ESPAÇO pausar/retomar, R reiniciar a interação.

## Onde está cada recurso gráfico
| Requisito | Arquivo / classe / função |
|---|---|
| R1 Modelos | `src/entities/submarino.py`, `disco_voador.py` |
| R2 Animação e interação (delta time) | `src/interaction/abducao.py` |
| R3 Translação, rotação, escala, hierarquia | `src/entities/*` |
| R4 Câmera e pausa | `src/controls/camera_rig.py`, `main.py` |
| R5 Textura | `src/environment/tanque.py` (`build_tanque`), `framework/material/texture.py` |
| R6 Iluminação e normais | ___ |
| R7 Shadow mapping | ___ e `shaders/` |
| Shaders / atributos / uniforms | `shaders/` (explicar na apresentação) |

## Contribuições individuais
- ___:
- ___:

## Fontes consultadas
- STEMKOSKI, Lee; PASCALE, Michael. Developing graphics frameworks with Python and OpenGL. CRC Press, 2022.
- Textura de teste `assets/textures/concreto_teste.png`: padrão sintético criado neste projeto com NumPy/Pygame, sem fonte externa. Substituir por uma foto de azulejo/concreto real na versão final.

## Declaração de uso de IA
Ferramenta: ___ | Finalidade: ___ | Trechos: ___
