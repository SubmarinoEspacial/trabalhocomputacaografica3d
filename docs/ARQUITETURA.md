# Arquitetura

- `main.py`: loop principal e montagem da cena.
- `src/interaction/abducao.py`: máquina de estados (lógica pura, testável sem OpenGL).
- `src/entities/`: estado de animação e modelo hierárquico de cada personagem.
- `src/environment/`: tanque de testes (chão, paredes, luz).
- `src/controls/`: câmera e pausa.
- `shaders/`: GLSL (vertex/fragment, passe de sombra).
- `assets/textures/`: imagens (registrar a origem no README).
- `framework/`: componentes copiados do livro.
