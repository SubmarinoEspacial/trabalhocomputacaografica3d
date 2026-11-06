# Trabalho Prático de Computação Gráfica (UNIPAC, 2026/02)

## Integrantes e temas
- Integrante 1: ___ (tema: ___)
- Integrante 2: ___ (tema: ___)
(Submarino Estilizado e Disco Voador)

## Descrição da cena e da interação
Mar aberto com fundo de areia, neblina no horizonte, ondas procedurais e sombras
projetadas na água. O submarino navega submerso, emerge com brilho emissivo, é
detectado pelo disco voador, inspecionado em órbita, iluminado por um feixe e
abduzido. Ao final, a cena reinicia.
Sequência: Submerso, Emergindo, Detecção, Posicionamento, Inspeção, Feixe, Abdução, Final.

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
| R5 Textura de areia | `src/environment/mar.py` (`build_mar`), `framework/core/texture.py`, `framework/material/texture.py` |
| R6 Ondas, shading e sombra da água | `src/environment/mar.py` (`water_height`, `water_slope`), `shaders/water.vert`, `shaders/water.frag` |
| R7 Iluminação | `framework/light/ambient.py`, `framework/light/directional.py`, `framework/material/phong.py`, `framework/material/lambert.py` |
| R8 Sombras projetadas | `framework/light/shadow_map.py`, `shaders/depth.vert`, `shaders/depth.frag`, `shaders/water.frag` |
| R9 Glow emissivo | `src/entities/submarino.py` (`glow`), `shaders/material.frag` (`u_emissive_strength`) |
| Shader / uniforms | `shaders/material.vert`, `shaders/material.frag`, `shaders/water.vert`, `shaders/water.frag` |

## Contribuições individuais
- ___:
- ___:

## Fontes consultadas
- STEMKOSKI, Lee; PASCALE, Michael. Developing graphics frameworks with Python and OpenGL. CRC Press, 2022.
- Areia `assets/textures/areia_procedural.png`: padrão procedural 256 × 256 gerado neste projeto com NumPy/Pygame, sem fonte externa. Substituir por fotografia licenciada de areia antes da entrega final.

## Declaração de uso de IA
Ferramenta: ___ | Finalidade: ___ | Trechos: ___
