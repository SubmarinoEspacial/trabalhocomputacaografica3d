# Arquitetura

- `main.py`: loop principal e montagem da cena.
- `src/interaction/abducao.py`: máquina de estados (lógica pura, testável sem OpenGL).
- `src/entities/`: estado de animação e modelo hierárquico de cada personagem.
- `src/environment/mar.py`: fundo marinho, grade de água, ondas e amostragem CPU.
- `src/controls/`: câmera e pausa.
- `shaders/`: GLSL da superfície, água e passe de sombra.
- `assets/textures/`: imagens (registrar a origem no README).
- `framework/`: implementações locais organizadas segundo os conceitos do livro.
