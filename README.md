# Trabalho Prático de Computação Gráfica (UNIPAC, 2026/02)

## Integrantes e temas
- Integrante 1: ___ (tema: ___)
- Integrante 2: ___ (tema: ___)
(Submarino Estilizado e Disco Voador)

## Descrição da cena e da interação
Mar aberto noturno com lua, estrelas, neblina no horizonte, ondas procedurais,
espuma e sombras projetadas na água. O submarino navega submerso, emerge com
brilho emissivo, é detectado pelo disco voador, inspecionado em órbita, iluminado
por um feixe e abduzido. O disco tem luzes coloridas, luzes pontuais dinâmicas e
um anel de impacto na superfície; o passe final aplica bloom e vinheta. Ao final,
a cena reinicia.
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
W/A/S/D mover, Q/E subir/descer, setas girar, ESPAÇO pausar/retomar, R reiniciar a interação, Esc sair.

## Onde está cada recurso gráfico
| Requisito | Arquivo / classe / função |
|---|---|
| R1 Modelos | `src/entities/submarino.py`, `disco_voador.py` |
| R2 Animação e interação (delta time) | `src/interaction/abducao.py` |
| R3 Translação, rotação, escala, hierarquia | `src/entities/*` |
| R4 Câmera e pausa | `src/controls/camera_rig.py`, `main.py` |
| R5 Textura de areia | `src/environment/mar.py` (`build_mar`), `framework/core/texture.py`, `framework/material/texture.py` |
| R6 Ondas, shading e sombra da água | `src/environment/mar.py` (`water_height`, `water_slope`), `shaders/water.vert`, `shaders/water.frag` |
| R7 Iluminação | `framework/light/ambient.py`, `framework/light/directional.py`, `framework/material/phong.py`, `framework/material/lambert.py`, `src/environment/night_materials.py` |
| R8 Sombras projetadas | `framework/light/shadow_map.py`, `src/environment/shadow.py`, `shaders/depth.vert`, `shaders/depth.frag`, `shaders/water.frag` |
| R9 Glow emissivo | `src/entities/submarino.py` (`glow`), `src/environment/effects.py`, `shaders/material.frag` (`u_emissive_strength`) |
| Atmosfera noturna e lua | `src/environment/sky.py`, `shaders/sky.vert`, `shaders/sky.frag`, `src/config.py` |
| Luzes pontuais e anel do feixe | `src/environment/point_light.py`, `src/environment/effects.py`, `src/entities/efeitos.py`, `shaders/material.frag`, `shaders/water.frag` |
| Espuma de contato e esteira | `src/environment/foam.py`, `shaders/foam.vert`, `shaders/foam.frag` |
| Pós-processamento | `src/environment/postprocess.py`, `shaders/postprocess.vert`, `shaders/postprocess.frag` |
| Shader / uniforms | `shaders/*.vert`, `shaders/*.frag` |

## Contribuições individuais
- ___:
- ___:

## Fontes consultadas
- STEMKOSKI, Lee; PASCALE, Michael. Developing graphics frameworks with Python and OpenGL. CRC Press, 2022.
- `assets/textures/areia_beach_sandy_shore_cc0.jpg`: fotografia `Beach sandy shore seamless ground texture.jpg`, de Sisters.seamless, Wikimedia Commons, licenciada como [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) ([página do arquivo](https://commons.wikimedia.org/wiki/File:Beach_sandy_shore_seamless_ground_texture.jpg)); redimensionada para 2048 × 2048 para o fundo marinho.
- Texturas `ceu_estrelado_procedural.png`, `lua_procedural.png`, `espuma_procedural.png`, `pintura_submarino_procedural.png`, `paineis_disco_procedural.png` e `feixe_ruido_procedural.png`: geradas proceduralmente neste projeto com Python/PIL, sem fonte externa. O histórico completo está em `docs/USO_IA.md`.

## Declaração de uso de IA
Ferramenta: opencode (modelo deepseek-v4.1-flash-free) | Finalidade: apoio na implementação, revisão e documentação | Trechos: ver `docs/USO_IA.md`.
