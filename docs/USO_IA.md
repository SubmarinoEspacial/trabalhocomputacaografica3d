# Registro de uso da IA

## Alinhamento inicial
- **Feito:** registradas as regras e o contexto do projeto para orientar as próximas tarefas.
- **Arquivos/funções criados ou revisados:** criado este arquivo; nenhum código do projeto foi alterado.
- **Regras a preservar:** compor personagens somente com geometrias e hierarquia `Object3D` do framework; usar delta time em movimentos; não implementar física nem detecção de colisão; comentar didaticamente em português; não alterar a máquina de estados sem solicitação. Adaptações do framework devem citar a fonte no comentário.

## Validacao inicial do framework e da janela
- **Feito:** inventariados os módulos do framework; criada uma `Base` provisória própria e a demonstração `DemoCubo`, com rotação baseada em delta time.
- **Arquivos/funções criados ou revisados:** criado `framework/core/base.py` (`Base.initialize`, `Base.update`, `Base.run`); revisado `main.py` (`DemoCubo.initialize`, `DemoCubo.update`, `DemoCubo._desenhar_cubo`); atualizado este registro.
- **Módulos ausentes nas pastas do framework:** `Base` do livro, `Matrix`, `Object3D`, `Mesh`, `Scene`, `Camera`, `Renderer`, `Texture`, `RenderTarget`, geometrias, materiais e luzes. Todas as pastas verificadas contêm somente `__init__.py`.
- **Verificação:** sintaxe e diagnósticos sem erros; teste OpenGL executou três quadros e confirmou avanço do ângulo para `4,32` graus. Dependências instaladas no ambiente local `.venv`.
- **Observação:** a `Base` criada é um bootstrap local de validação, não uma implementação copiada/adaptada do livro. O workspace não contém índice do livro que permita atribuir cada módulo a um capítulo específico.
- **Execução:** `.venv/bin/python main.py` (fechar a janela ou pressionar `Esc`).

## Publicacao no GitHub
- **Feito:** projeto publicado no branch `main` do repositório informado, no commit `ead412a`; verificados o conteúdo local e a ausência de padrões de credenciais nos arquivos enviados.
- **Arquivos/funções criados ou revisados:** nenhum código alterado nesta tarefa; atualizado este registro.
- **Destino:** `https://github.com/SubmarinoEspacial/trabalhocomputacaografica3d`.

## Câmera, pausa e reset
- **Feito:** estruturada `Aplicacao` sobre `Base`, com projeção em perspectiva, controles de câmera, alternância de pausa por ESPAÇO e reset do controlador por R. Atualização e aplicação dos modelos ficam condicionadas às raízes estarem construídas.
- **Arquivos/funções criados ou revisados:** revisado `main.py` (`Aplicacao.initialize`, `Aplicacao.update`, `Aplicacao._modelos_construidos`); criado `src/controls/camera_rig.py` (`MovementRig.update`, `MovementRig.apply`); atualizado este registro.
- **Fonte da adaptação:** Stemkoski e Pascale (2022), capítulo 4, seção "Scene Graph Framework", classe `MovementRig`.
- **Verificação:** teste OpenGL de cinco quadros confirmou câmera ativa durante a pausa, cubo parado e reset por R; `tests.test_abducao` passou em 30 e 120 FPS; diagnósticos Pylance sem erros.

## Tanque e textura
- **Feito:** criado o tanque com piso UV repetível e quatro paredes de caixa; conectada a renderização da cena à aplicação; removido o bloco de demo de cubo duplicado em `main.py`.
- **Arquivos/funções criados ou revisados:** criado `src/environment/tanque.py` (`build_tanque`), `framework/core/object3d.py`, `framework/core/mesh.py`, `framework/core_ext/scene.py`, `framework/geometry/primitives.py`, `framework/material/basic.py` e `framework/material/texture.py`; revisado `main.py`; atualizado `README.md` e este registro.
- **Origem do asset:** `assets/textures/concreto_teste.png` é uma textura sintética de 256 × 256 px, gerada com NumPy/Pygame, sem fonte externa; trocar por foto real antes da entrega final.
- **Fonte conceitual:** estrutura de cena conforme capítulo 4 e mapeamento de textura conforme capítulo 5 de Stemkoski e Pascale (2022); implementações locais originais, sem cópia de código do livro.
- **Verificação:** renderização real gerou cinco malhas e 445 cores distintas na região capturada do piso, com `glGetError()` sem erros.

## Modelo do submarino
- **Feito:** implementados `Submarino.build()` e `Submarino.apply()` com casco cilíndrico ao longo de X, proa, torre, periscópio, hélice de três pás, aletas e leme em hierarquia `Object3D`; o root entra na cena e atualiza em cada quadro.
- **Arquivos/funções criados ou revisados:** revisado `src/entities/submarino.py`; adicionada `CylinderGeometry` em `framework/geometry/primitives.py`; revisado `main.py` para construir/adicionar o root e atualizar a lógica enquanto o submarino estiver construído.
- **Verificação:** em oito quadros OpenGL, a posição de patrulha avançou de `x=-7,976` para `x=-7,713` e o pivô da hélice girou `65,7°`; a captura mostrou o submarino no tanque. `tests.test_abducao` passou em 30 e 120 FPS.
