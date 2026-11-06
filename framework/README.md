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
