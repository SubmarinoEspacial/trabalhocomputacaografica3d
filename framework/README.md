# framework/

As pastas seguem a organização do framework apresentado por Stemkoski e Pascale
(2022). Os componentes deste workspace são implementações locais originais para
o projeto, não cópias do código do livro. A cena utiliza `core/object3d.py`,
`core/mesh.py`, `core_ext/scene.py`, `geometry/primitives.py` (plano, caixa,
cilindro, esfera e cone) e `material/texture.py`; `Object3D.visible` oculta ramos
inteiros. A iluminação Lambert usa `light/directional.py` e um shader único em
`material/lambert.py`; as normais das geometrias alimentam o cálculo difuso.
`light/shadow_map.py` executa os dois passes de shadow mapping com shaders em
`shaders/`. Os comentários registram as fontes conceituais sem copiar código.

## Inventário da revisão
- **Presentes e usados:** `core.Base`, `Object3D`, `Mesh`, `Scene`, `Texture`, `DepthRenderTarget`, `ShadowCamera`; geometrias `PlaneGeometry`, `BoxGeometry`, `CylinderGeometry`, `SphereGeometry`, `ConeGeometry`; `TextureMaterial`, `LambertMaterial`, `PhongMaterial`, `DepthMaterial`, `Light`, `AmbientLight`, `DirectionalLight` e shadow map.
- **Substitutos parciais:** `DepthRenderTarget` é depth-only, não o `RenderTarget` genérico do livro; `LightingContext` e `ColorMaterial` não substituem a arquitetura completa de `Renderer`/`UniformList`.
- **Ausentes:** `OpenGLUtils`, `Attribute`, `Uniform`, `Matrix`, `Camera`, `Renderer` dedicado e `PointLight`. A aplicação atual usa `MovementRig` e `ShadowMap` próprios.
- **Sem implementação para remover:** `extras/__init__.py`, os marcadores `__init__.py` e `shaders/.gitkeep` são vazios; não há módulos funcionais copiados e sem uso. `depth.vert/.frag` estão ativos.
- **Convenção:** nenhuma API existente do diretório foi renomeada; aliases camelCase são acrescentados sem remover os nomes atuais quando necessários.
