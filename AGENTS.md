# AGENTS.md

Academic OpenGL scene (Pygame + PyOpenGL, GLSL 120, legacy fixed-function matrices). Comments, docstrings, docs and commit messages are in Portuguese; keep that convention.

## Commands
- Setup: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`. Local `venv/` and `.venv/` both exist in this checkout (both gitignored); `venv/bin/python` works without activating.
- Run: `venv/bin/python main.py` (needs a display/OpenGL context; the abduction cycle runs automatically). `--quality minima|baixa|media|alta` (or `--qualidade`, also `--quality=alta`) picks the quality profile at startup; default `media`. `--profile`/`--perfilar` enables the F2 diagnostics overlay from launch.
- Test: `venv/bin/python -m tests.test_abducao` and `venv/bin/python -m tests.test_camera`, both from the repo root. Plain asserts, no pytest/unittest, no OpenGL context; must run as modules (`python tests/test_abducao.py` fails with `No module named 'src'`). Both verified passing. Smoke syntax check without a display: `venv/bin/python -m compileall -q main.py src tests framework/core/base.py`.
- No lint, formatter, typecheck or CI config; `pyrightconfig.json` only adds `framework/` to Pyright paths.

## Controls & HUD
- The binding list lives in `config.CONTROLS` and is the single source read by the HUD (`src/ui/hud.py`) and mirrored in the README table; H toggles it in-app. The key codes themselves live once in `config.KEYMAP` (pygame constants); `main.py` and `camera_rig.py` read them from `C.KEYMAP`. If you add or rename a key, update `KEYMAP`, `CONTROLS` and the README table.
- Non-obvious keys: Esc never quits (closes the About panel if open, else exits fullscreen; close the window to exit). F2 toggles the per-stage timings panel. F3/F4/F5/X select the baixa/média/alta/mínima quality profiles instantly — manual choice turns the adaptive mode off (HUD shows `Qualidade: … (manual)`; G re-enables it as `auto`) and a `Qualidade: …` toast shows for ~1.5 s. Only uniforms/flags apply at runtime (render scale, shadow depth map recreation, PCF, water wave count, point lights, bloom); water grid, model tessellation, disc ring lights and DETALHES_COMPLETOS apply only on restart. V toggles the FPS limiter (`clock.tick`); T switches the 60/120 FPS target; G toggles adaptive quality; L toggles `PRESENT_MODE` in real time without recreating the scene; SHIFT multiplies horizontal movement.
- The HUD is drawn last as an ortho overlay — not in the shadow pass, not in the postprocess FBO.

## Import quirk
- `framework/` is not a package. `main.py` inserts `framework/` at `sys.path[0]`; `src/__init__.py` does the same for anything importing `src.*`. Framework modules import each other as top-level names (`core.*`, `core_ext.*`, `light.*`, `material.*`, `geometry.*`). `Scene` and `DepthRenderTarget` live in `core_ext`, not `core`. Never rewrite imports as `framework.core...`; new standalone scripts must import `src` (or add `framework/` to `sys.path`) before importing framework modules.
- PyOpenGL error checking/logging flags are read at import time. `main.py` sets `OpenGL.ERROR_CHECKING = False` (and the logging flags) before `import OpenGL.GL` because `C.DEBUG_GL = False`; new scripts that import GL modules must set these before the import, or flip `DEBUG_GL` in `config.py` for debugging.

## Architecture
- `main.py` (`Aplicacao(Base)`) wires lighting, shadow map, camera rig, postprocess, scene, entities and controller. Frame order matters: shadow depth pass -> color `PostProcess.begin()` -> `camera_rig.apply()` -> `Scene.render()` (opaque, then transparent with depth writes disabled) -> `PostProcess.end()`; the HUD is drawn after `end()`.
- `src/interaction/abducao.py` is pure OpenGL-free logic driven by delta time; `AbducaoController.reset()` also resets both entities. `tests/test_abducao.py` locks the state sequence, surface tracking, glow, scale and reset.
- `src/config.py` holds every tunable; change values there, not inside animation code. It parses `sys.argv` at import time and applies the quality profile immediately (`aplicar_perfil_qualidade(QUALITY)` on import). README.md maps each assignment requirement to files.
- Water equations exist twice and must stay in sync: CPU `water_height`/`water_slope` in `src/environment/mar.py` and GPU `shaders/water.vert`. Both use `(C.WATER_WAVES + C.WATER_DETAIL_WAVES)[:C.WATER_WAVE_COUNT]`; the GPU upload is split — `framework/material/water.py` uploads the 3 main waves, `src/environment/night_materials.py` uploads the 2 detail waves (`u_wave3`/`u_wave4`) and `u_wave_count`/`u_pcf_samples`.
- More context: `docs/ARQUITETURA.md` (per-module map), `framework/README.md` (component inventory), `docs/USO_IA.md` (change history).

## Framework conventions
- Keep existing snake_case public names; camelCase methods are aliases (`Base.deltaTime`, `Object3D.setPosition`, `LightingContext.setShadowMap`). Add aliases instead of renaming APIs.
- Node shadow flags are recursive: `setCastShadow` / `setReceiveShadow`. `Mesh.draw` selects passes via `material.transparent` and node `castShadow`; transparent objects need `transparent=True`.
- Shaders in `shaders/` are read at runtime by `framework/material/{lambert,water,depth}.py` and others; there is no hot reload, restart after editing them.
- The view math of `MovementRig` (now `CameraRig`; the alias is kept) is duplicated in `_camera_view_matrix` in `framework/light/shadow_map.py`; update both if camera yaw/pitch/position semantics change.

## Project rules
- Compose characters only from framework geometries and `Object3D` hierarchy; use delta time for motion; no physics or collision detection; do not change the state machine without being asked.
- Cite Stemkoski & Pascale (2022) in comments when adapting framework concepts.
- After AI-assisted changes, append a section to `docs/USO_IA.md` following its existing format (`Feito:` / `Arquivos:` or `Arquivos/funções criados ou revisados:` / `Verificação:`).
- `assets/textures/areia_beach_sandy_shore_cc0.jpg` is a licensed CC0 sand photograph sourced from Wikimedia Commons (see README for attribution); do not replace it with an unlicensed image.
- Do not commit unless explicitly asked.
