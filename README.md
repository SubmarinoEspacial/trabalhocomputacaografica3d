# Trabalho Prático de Computação Gráfica (UNIPAC, 2026/02)

## Integrantes e temas
- Integrante 1: ___ (tema: ___)
- Integrante 2: ___ (tema: ___)
(Submarino Estilizado e Disco Voador)

## Descrição da cena e da interação
Mar aberto noturno com lua, estrelas, neblina no horizonte, ondas procedurais,
espuma e sombras projetadas na água. O submarino navega submerso, emerge com
brilho emissivo, é detectado pelo disco voador, inspecionado em órbita, iluminado
por um feixe e abduzido. O disco tem luzes emissivas brancas e brilhantes, luzes pontuais dinâmicas brancas e
um anel de impacto na superfície; o passe final aplica bloom e vinheta. Ao final,
a cena reinicia.
Sequência: Submerso, Emergindo, Detecção, Posicionamento, Inspeção, Feixe, Abdução, Final.

### Iluminação e modo apresentação
A cena é noturna, com lua direcional, luz ambiente fria e shadow mapping. Os veículos usam, por
padrão, um modo apresentação (`PRESENT_MODE = 1`): ambiente hemisférico (céu→mar), luz de
preenchimento fria sem sombra do lado oposto à lua, contorno Fresnel azul-prateado e neblina
atenuada nos veículos; o tone mapping dos veículos é Reinhard (`cor / (cor + 1)`) com exposição
própria (`PRESENT_VEHICLE_EXPOSURE`), preservando o céu e o mar escuros e as sombras da lua.
Tudo é cálculo no fragment shader (`shaders/material.frag`), sem objetos de luz ou passes
adicionais; a areia e o restante do cenário seguem o caminho normal do shader. `L` alterna o
modo em tempo real. Parâmetros em `src/config.py` (`PRESENT_*` e `SUB_COLOR_*`/`DISC_COLOR_*`).

## Instalação e execução
```
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python main.py
```
Teste da máquina de estados (sem OpenGL): `python -m tests.test_abducao`

## Controles
A mesma lista pode ser exibida no HUD com H e é definida em `src/config.py` (`CONTROLS`).

| Tecla | Ação |
|---|---|
| W/A/S/D | Mover a câmera |
| Q / E | Subir / descer |
| Setas | Girar a câmera |
| ESPAÇO | Pausar / retomar a animação |
| R | Reiniciar a interação |
| F1 | Mostrar / ocultar todo o HUD |
| F2 | Perfil de qualidade média |
| F3 | Mostrar / ocultar os tempos (FPS, lógica, sombra, render) |
| F4 | Perfil de qualidade alta |
| F5 | Perfil de qualidade baixa |
| F11 / Alt+Enter | Alternar janela / tela cheia |
| ESC | Sair da tela cheia / fechar o painel Sobre |
| H | Mostrar / ocultar a lista de controles |
| I | Abrir / fechar o painel Sobre o projeto |
| L | Alterna o modo apresentação (iluminação de realce dos veículos) |
| V | Alterna o limitador de FPS (alvo atual / sem limite) |
| T | Alterna o alvo entre 60 e 120 FPS |
| G | Liga / desliga a qualidade adaptativa |

O HUD é discreto: uma linha com FPS, tempo de quadro, estado e alvo no canto superior esquerdo,
seguida de qualidade/escala e do modo adaptativo. A lista de controles fica escondida por padrão
(dica `H controles | I sobre | F1 ocultar`); H abre as duas colunas e F1 oculta todo o HUD. O botão
"? Sobre" no canto superior direito abre um painel pequeno com resumo, sequência, técnicas, créditos
e referência (também por I; fecha por I, ESC, botão Fechar ou clique fora). Com F3, o HUD acrescenta
o diagnóstico (GL, janela, sombra, PCF, luzes, draw calls, água e tempos por etapa). O VSync não é
recriado após a janela existir — V controla o `clock.tick` e T troca o alvo 60/120.

A fonte do HUD escala com a altura da janela (`HUD_SCALE`, padrão `1.0`; ~1,5% da altura, entre
11 e 18 px). Os textos estáticos são enviados à GPU uma única vez; só a linha de FPS é reconstruída
a cada 0,5 s.

## Janela redimensionável
A janela é criada com `pygame.RESIZABLE`, aceita arrastar as bordas para aumentar ou diminuir e
respeita o tamanho mínimo definido em `config.py` (`MIN_WINDOW_SIZE = (640, 360)`). Ao redimensionar,
a aplicação atualiza `glViewport`, a razão de aspecto em `gluPerspective`, o tamanho do framebuffer de
pós-processamento e o tamanho guardado na Base. O mapa de sombra não é recriado e permanece com
tamanho fixo. Tamanho inicial: `WINDOW_SIZE = (960, 540)`. O botão da janela é o único meio de fechar.

Para tela cheia de alto custo, `RENDER_SCALE` (padrão `1.0`) permite renderizar a cena em um
framebuffer menor e ampliar para a tela inteira; a qualidade adaptativa usa `0.85`, `0.70` e `0.50`
quando o FPS fica abaixo de 90% do alvo por 2 s. O mapa de sombra continua independente dessa escala.

## Desempenho e perfis de qualidade
O padrão é `media`; também é possível escolher no arranque com `--quality baixa|media|alta`
(`--qualidade` também funciona). F2/F4/F5 trocam o perfil em tempo real, recriando a sombra
e a cena e reiniciando a sequência; o estado do limitador escolhido com V é preservado.
T alterna o alvo entre 60 e 120 FPS e G liga/desliga a qualidade adaptativa. A janela usa
`WINDOW_SIZE` por padrão.

Medição na Intel Iris Xe (Mesa 25.2.8, GL 4.6 Compatibility), F3 ligado, adaptação desligada
e V sem limite para medir a capacidade real:

| Perfil | Janela 960×540 (alvo 60) | Janela sem limite | Tela cheia 1920×1080 (alvo 60) | Tela cheia sem limite |
|---|---|---|---|---|
| `baixa` | 60–62 FPS | ~280 FPS | 60–62 FPS | ~165–180 FPS |
| `media` | 60–62 FPS | ~280–300 FPS | 60–62 FPS | ~170–180 FPS |
| `alta` | 60–62 FPS | ~200–220 FPS | 60–62 FPS (alvo 120: ~120) | ~128–135 FPS |

Antes desta rodada, `media` em 960×540 ficava em ~28–31 FPS (frame ~33–35 ms; principal
29–32 ms; sombra 3,1–3,5 ms). Depois do cache de geometria e uniforms, o passe principal
caiu para ~1,8–2,3 ms e a sombra para ~0,65–0,8 ms na janela; a tela cheia em `alta` fica em
~7,5 ms de CPU, ainda acima de 120 FPS de capacidade. O HUD custa ~0,07 ms por quadro
(0,10 ms ligado contra 0,03 ms oculto no contador), bem abaixo de 1 FPS no alvo de 60.

| Perfil | Sombra | PCF | Água | Ondas | Luzes pontuais | Detalhes | Bloom | Geometria |
|---|---|---|---|---|---|---|---|---|
| `baixa` | 1024 | 1 amostra | 80 × 80 | 2 | 2 | ocultados | desligado | 8/6 segmentos/anéis |
| `media` | 1024 | 4 amostras (2 × 2) | 80 × 80 | 3 | 2 | ocultados; luzes do anel: 8 | desligado | 12/8 segmentos/anéis |
| `alta` | 2048 | 9 amostras (3 × 3) | 200 × 200 | 5 | 4 | completos; luzes do anel: 16 | ligado em 1/4 de resolução | 32/16 segmentos/anéis |

No `media`, o total aproximado de meshes visíveis ficou em 84–89 (somente os modelos
principais entram no passe de sombra, 8 draws); em `alta`, 122–127. O alvo original de
menos de 60 draw calls no passe principal não foi necessário depois do cache: o custo de
CPU dos 84–127 draws ficou abaixo de ~1 ms, e todos os perfis passam de 60 FPS. O perfil
`alta` é destinado à apresentação visual; `baixa` e `media` mantêm os requisitos de dois
modelos, hierarquia, estados, pausa, textura UV, luz direcional com normais e shadow
mapping atualizado.

A qualidade adaptativa reduz um degrau após 2 s abaixo de 90% do alvo e sobe após 5 s
acima de 110%, na ordem escala de render → PCF → ondas da água → luzes pontuais → bloom.
Ela só altera uniforms, alvos de pós-processamento e parâmetros lidos por frame; nenhuma
malha é recriada.

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
