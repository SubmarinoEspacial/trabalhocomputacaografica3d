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

## Modelo do disco voador
- **Feito:** implementados `DiscoVoador.build()` e `apply()` com corpo esférico achatado, cúpula, pivô com oito luzes, cone de feixe oculto quando desligado e escala ligada ao nível do feixe; root adicionado à cena.
- **Arquivos/funções criados ou revisados:** revisado `src/entities/disco_voador.py`; adicionadas `SphereGeometry`, `ConeGeometry` e visibilidade recursiva em `framework/geometry/primitives.py` e `framework/core/object3d.py`; revisado `main.py`; atualizado este registro e `framework/README.md`.
- **Verificação:** ciclo simulado percorreu PATRULHA a FINAL e reiniciou; o anel girou, o hover foi aplicado e o feixe ficou visível durante FEIXE/ABDUCAO e apagou no reset. Captura OpenGL mostrou disco e submarino juntos.

## Revisão visual do ciclo
- **Feito:** executado e capturado o ciclo completo em OpenGL, incluindo quatro quadrantes da órbita, início/fim do feixe, subida e reinício.
- **Valor alterado em `src/config.py`:** `ABDUCT_SPIN` de `2.0` para `math.pi / 4` rad/s. Com subida de 4 s, isso reduz a rotação de 8 rad (1,27 voltas, rápida) para aproximadamente 3,17 rad (meia-volta, gradual e legível).
- **Valores mantidos:** `FLEE_TIME`, `DISC_SPEED`, `ORBIT_RADIUS`, `ORBIT_OMEGA`, `BEAM_TIME`, `ABDUCT_TIME`, `ABDUCT_RISE` e `ABDUCT_MIN_SCALE` mantiveram posicionamento, órbita, feixe e subida coerentes nas capturas.
- **Verificação:** ordem completa dos estados confirmada; durante FEIXE o submarino permanece em `y=1` com feixe em `0,55`; a meio da abdução está em `y=2,25`, escala `0,7` e yaw `pi/2`; o reinício restaura a cena. Nenhuma lógica foi alterada.

## Iluminação direcional
- **Feito:** criada uma única `DirectionalLight` em `main.py` (`setup_luz`) e um `LightingContext`/shader Lambert compartilhado por piso, paredes, submarino e disco.
- **Arquivos/funções criados ou revisados:** criados `framework/light/directional.py` e `framework/material/lambert.py`; revisados `framework/material/basic.py`, `framework/material/texture.py`, `framework/geometry/primitives.py`, `src/environment/tanque.py`, `src/entities/submarino.py`, `src/entities/disco_voador.py`, `main.py`, `README.md` e `framework/README.md`.
- **Explicação no código:** uniforms `u_light_direction_eye`, `u_light_ambient`, `u_light_diffuse`, `u_material_color`, `u_use_texture` e `u_texture`; transformação das normais pelo `gl_NormalMatrix`; difuso Lambert pelo produto normal-luz. O comentário diferencia sombreamento local de sombra projetada, que exige shadow map/depth pass.
- **Fonte conceitual:** Stemkoski e Pascale (2022), capítulo 6, "Lights"; implementação GLSL original do projeto.
- **Verificação:** shader compilado no OpenGL 4.6 Compatibility Profile; cena completa renderizou 7 malhas sem erro GL; uma caixa cinza produziu intensidades distintas em faces com normais diferentes (`83` e `201`); `tests.test_abducao` passou.

## Iluminação Lambert
- **Feito:** definida uma luz direcional em `main.py` (`setup_luz`) e compartilhado um único shader Lambert por materiais de cor e textura para tanque, submarino e disco.
- **Arquivos/funções criados ou revisados:** criados `framework/light/directional.py` e `framework/material/lambert.py`; revisados `framework/material/basic.py`, `framework/material/texture.py`, `framework/geometry/primitives.py`, `src/environment/tanque.py`, `src/entities/submarino.py`, `src/entities/disco_voador.py`, `main.py`, `README.md` e `framework/README.md`.
- **Conceitos documentados no código:** uniforms da luz e do material, transformação das normais para o espaço visual, difuso Lambert por produto escalar; sombreamento local não equivale a sombra projetada, que exige shadow map/depth pass.
- **Verificação:** shader compilado no OpenGL 4.6 Compatibility Profile; cena completa renderizou sem erro GL; uma caixa de cor uniforme produziu intensidades distintas em faces com normais diferentes (`(83,83,81)` e `(201,195,181)`).

## Shadow mapping
- **Feito:** implementado passe ortográfico da luz para depth texture e passe Lambert normal com comparação 3×3 PCF e bias ajustado pela orientação da face.
- **Arquivos/funções criados ou revisados:** criado `framework/core_ext/render_target.py` (`DepthRenderTarget`), `framework/light/shadow_map.py` (`ShadowMap.render`), `shaders/depth.vert` e `shaders/depth.frag`; revisados `framework/material/lambert.py`, `main.py`, `README.md` e este registro.
- **Uniforms e atributos:** comentários nos shaders descrevem `gl_Vertex`, matrizes built-in, `u_light_view_projection_eye`, uniforms da luz/material, depth sampler, texel size, bias e flag de sombra. O passe de depth não declara uniforms próprios; o depth test grava `gl_FragCoord.z`.
- **Verificação:** FBO completo e shaders de depth compilados no driver; máscara no piso mudou de 2.662 pixels na patrulha para 568 na subida, e o centro mudou de `[278,214]` para `[292,515]`; nenhum erro GL.
