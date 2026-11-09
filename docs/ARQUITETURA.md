# Arquitetura

- `main.py`: loop principal, montagem da cena e ordem dos passes (sombra, framebuffer de cor, pós-processamento).
- `src/interaction/abducao.py`: máquina de estados (lógica pura, testável sem OpenGL).
- `src/entities/`: estado de animação e modelo hierárquico do submarino, do disco e do anel de impacto.
- `src/environment/mar.py`: fundo marinho, grade de água, ondas e amostragem CPU.
- `src/environment/sky.py`: domo de estrelas e lua, acompanhando a câmera.
- `src/environment/shadow.py`: câmera/mapa de sombra lunar que segue a ação.
- `src/environment/night_materials.py`: exposição, gamma, neblina e luzes pontuais nos materiais.
- `src/environment/point_light.py`: descrição das luzes pontuais dinâmicas.
- `src/environment/foam.py`: espuma de contato e esteira do submarino.
- `src/environment/effects.py`: materiais aditivos do feixe e do anel de impacto.
- `src/environment/postprocess.py`: framebuffer de cor, bloom e vinheta.
- `src/controls/camera_rig.py`: câmera e controles de movimento; pausa e reset ficam em `main.py`.
- `shaders/`: GLSL de superfície, água, céu, espuma, feixe, impacto, depth e pós-processamento.
- `assets/textures/`: imagens; a origem de cada textura está no README.
- `framework/`: implementações locais organizadas segundo os conceitos do livro.
