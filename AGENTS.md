# AGENTS.md

Academic OpenGL scene (Pygame + PyOpenGL, GLSL 120, legacy fixed-function matrices). Comments, docstrings, docs and commit messages are in Portuguese; keep that convention.

## Commands
- Setup: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`. A local `venv/` already exists in this checkout; use `venv/bin/python` when not activated.
- Run: `python main.py` (needs a display/OpenGL context; the abduction cycle runs automatically). Controls: W/A/S/D, Q/E, arrows, SPACE pause, R reset, Esc quit.
- Test: `python -m tests.test_abducao` from the repo root. Plain asserts, no pytest/unittest, and it must run as a module (direct `python tests/test_abducao.py` fails with `No module named 'src'`). It needs no OpenGL context.
- No lint, formatter, typecheck or CI config. `pyrightconfig.json` only adds `framework/` to Pylance/Pyright paths.

## Import quirk
- `framework/` is not a package. `src/__init__.py` and `main.py` insert it into `sys.path`, and its modules import each other as top-level names (`from core.mesh import Mesh`, `from light.directional import DirectionalLight`, `from material.lambert import LightingContext`). Never rewrite imports as `framework.core...`.
- New standalone scripts must import `src` (or add `framework/` to `sys.path`) before importing framework modules.

## Architecture
- `main.py` (`Aplicacao(Base)`) wires lighting, shadow map, camera rig, postprocess, scene, entities and controller. Frame order matters: shadow depth pass -> color `PostProcess.begin()` -> camera apply -> `Scene.render()` (opaque, then transparent with depth writes disabled) -> `PostProcess.end()`.
- `src/interaction/abducao.py` is pure OpenGL-free logic driven by delta time; `AbducaoController.reset()` also resets both entities. `tests/test_abducao.py` locks the state sequence, surface tracking, glow, scale and reset.
- `src/config.py` holds every tunable; change values there, not inside animation code. `README.md` maps each assignment requirement to files.
- Water equations exist twice: CPU `water_height`/`water_slope` in `src/environment/mar.py` and GPU in `shaders/water.vert`, both fed by `C.WATER_WAVES`. Keep formulas and parameters in sync.
- More context: `docs/ARQUITETURA.md`, `framework/README.md` (component inventory), `docs/USO_IA.md` (change history).

## Framework conventions
- Keep existing snake_case public names; camelCase methods are aliases (`Base.deltaTime`, `Object3D.setPosition`, `LightingContext.setShadowMap`). Add aliases instead of renaming APIs.
- Node shadow flags are recursive: `setCastShadow` / `setReceiveShadow`. `Mesh.draw` selects passes via `material.transparent` and node `castShadow`; transparent objects need `transparent=True`.
- Shaders in `shaders/` are read at runtime by `framework/material/{lambert,water,depth}.py`; there is no hot reload, restart after editing them.
- `MovementRig` view math is duplicated in `_camera_view_matrix` (`framework/light/shadow_map.py:128`); update both if camera yaw/pitch/position semantics change.

## Project rules
- Compose characters only from framework geometries and `Object3D` hierarchy; use delta time for motion; no physics or collision detection; do not change the state machine without being asked.
- Cite Stemkoski & Pascale (2022) in comments when adapting framework concepts.
- After AI-assisted changes, append a section to `docs/USO_IA.md` following its existing `Feito / Arquivos / Verificação` format.
- `assets/textures/areia_beach_sandy_shore_cc0.jpg` is a licensed CC0 sand photograph sourced from Wikimedia Commons (see README for attribution); do not replace it with an unlicensed image.
