# AGENTS.md

Academic OpenGL scene (Pygame + PyOpenGL, GLSL 120, legacy fixed-function matrices). Comments, docstrings, docs and commit messages are in Portuguese; keep that convention.

## Commands
- Setup: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`. Local `venv/` and `.venv/` both exist in this checkout (both gitignored); `venv/bin/python` works without activating.
- Run: `venv/bin/python main.py` (needs a display/OpenGL context; the abduction cycle runs automatically). `--quality baixa|media|alta` (or `--qualidade`, also `--quality=alta`) picks the quality profile at startup; default `media`. `--profile`/`--perfilar` enables the F3 diagnostics overlay from launch.
- Controls: W/A/S/D move, Q/E up/down, arrows rotate, SPACE pause, R reset, F1/F2/F4 switch quality profile (recreates shadow map + scene and restarts the cycle), F3 toggle diagnostic (FPS/timings printed once per second), F11 or Alt+Enter toggle fullscreen. Esc does NOT quit — it exits fullscreen if fullscreen, otherwise nothing; close the window to quit.
- Test: `python -m tests.test_abducao` from the repo root. Plain asserts, no pytest/unittest, and it must run as a module (direct `python tests/test_abducao.py` fails with `No module named 'src'`). It needs no OpenGL context. Verified passing.
- No lint, formatter, typecheck or CI config. `pyrightconfig.json` only adds `framework/` to Pylance/Pyright paths.

## Import quirk
- `framework/` is not a package. `src/__init__.py` and `main.py` insert it into `sys.path`, and its modules import each other as top-level names (`from core.mesh import Mesh`, `from light.directional import DirectionalLight`, `from material.lambert import LightingContext`). Never rewrite imports as `framework.core...`.
- New standalone scripts must import `src` (or add `framework/` to `sys.path`) before importing framework modules.

## Architecture
- `main.py` (`Aplicacao(Base)`) wires lighting, shadow map, camera rig, postprocess, scene, entities and controller. Frame order matters: shadow depth pass -> color `PostProcess.begin()` -> camera apply -> `Scene.render()` (opaque, then transparent with depth writes disabled) -> `PostProcess.end()`.
- `src/interaction/abducao.py` is pure OpenGL-free logic driven by delta time; `AbducaoController.reset()` also resets both entities. `tests/test_abducao.py` locks the state sequence, surface tracking, glow, scale and reset.
- `src/config.py` holds every tunable; change values there, not inside animation code. It parses `sys.argv` at import time and applies the quality profile immediately (`aplicar_perfil_qualidade(QUALITY)` on import). `README.md` maps each assignment requirement to files.
- Water equations exist twice and must stay in sync: CPU `water_height`/`water_slope` in `src/environment/mar.py` and GPU `shaders/water.vert`. Both use `(C.WATER_WAVES + C.WATER_DETAIL_WAVES)[:C.WATER_WAVE_COUNT]`; the GPU upload is split — `framework/material/water.py` uploads the 3 main waves, `src/environment/night_materials.py` uploads the 2 detail waves (`u_wave3`/`u_wave4`) and `u_wave_count`/`u_pcf_samples`.
- More context: `docs/ARQUITETURA.md` (per-module map), `framework/README.md` (component inventory), `docs/USO_IA.md` (change history).

## Framework conventions
- Keep existing snake_case public names; camelCase methods are aliases (`Base.deltaTime`, `Object3D.setPosition`, `LightingContext.setShadowMap`). Add aliases instead of renaming APIs.
- Node shadow flags are recursive: `setCastShadow` / `setReceiveShadow`. `Mesh.draw` selects passes via `material.transparent` and node `castShadow`; transparent objects need `transparent=True`.
- Shaders in `shaders/` are read at runtime by `framework/material/{lambert,water,depth}.py` and others; there is no hot reload, restart after editing them.
- `MovementRig` view math is duplicated in `_camera_view_matrix` (`framework/light/shadow_map.py:128`); update both if camera yaw/pitch/position semantics change.

## Project rules
- Compose characters only from framework geometries and `Object3D` hierarchy; use delta time for motion; no physics or collision detection; do not change the state machine without being asked.
- Cite Stemkoski & Pascale (2022) in comments when adapting framework concepts.
- After AI-assisted changes, append a section to `docs/USO_IA.md` following its existing format (`Feito:` / `Arquivos:` or `Arquivos/funções criados ou revisados:` / `Verificação:`).
- `assets/textures/areia_beach_sandy_shore_cc0.jpg` is a licensed CC0 sand photograph sourced from Wikimedia Commons (see README for attribution); do not replace it with an unlicensed image.
- Uncommitted work-in-progress may exist in the tree; do not commit unless explicitly asked.
