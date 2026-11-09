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
F1 perfil baixa, F2 perfil media, F4 perfil alta, F3 mostrar/ocultar diagnóstico (FPS e tempos).

## Desempenho e perfis de qualidade
O padrão é `media`; também é possível escolher no arranque com `--quality baixa|media|alta`
(`--qualidade` também funciona). F1/F2/F4 trocam o perfil em tempo real, recriando
a sombra e a cena com os novos parâmetros e reiniciando a sequência. A janela usa
960 × 540 por padrão (`WINDOW_WIDTH`/`WINDOW_HEIGHT` em `config.py`). Antes da
sintonia, a cena medida em uma Intel Iris Xe ficou em cerca de 10 FPS; após os cortes,
`baixa` ficou em torno de 36 FPS e `media` em torno de 29–31 FPS. `alta` preserva a
qualidade visual anterior (cerca de 12–13 FPS na mesma máquina).

| Perfil | Sombra | PCF | Água | Ondas | Luzes pontuais | Detalhes | Bloom | Geometria |
|---|---|---|---|---|---|---|---|---|
| `baixa` | 1024 | 1 amostra | 80 × 80 | 3 | 2 | ocultados | desligado | 8/6 segmentos/anéis |
| `media` | 1024 | 4 amostras (2 × 2) | 80 × 80 | 5 | 2 | ocultados; luzes do anel: 8 | ligado | 12/8 segmentos/anéis |
| `alta` | 2048 | 9 amostras (3 × 3) | 200 × 200 | 5 | 4 | completos; luzes do anel: 16 | ligado | 32/16 segmentos/anéis |

No `media`, o total aproximado de meshes visíveis ficou em 84–86 (somente os modelos
principais entram no passe de sombra). O perfil `alta` é destinado à apresentação visual;
`baixa` e `media` mantêm os requisitos de dois modelos, hierarquia, estados, pausa,
textura UV, luz direcional com normais e shadow mapping atualizado.

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
