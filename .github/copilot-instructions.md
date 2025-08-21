## Quick purpose
This file gives concise, actionable guidance for AI coding agents working in PlantGuard so they can be productive immediately.

## High-level architecture (read first)
- Code is packaged under `src/` (package root). Key subsystems:
  - Vision: `src/core/vision.py`, `src/core/huggingface_vision.py`, `src/core/models.py` (model loading & preprocessing)
  - Model management: `src/core/model_manager.py` (hot-swappable models; JSON-driven config at `config/models.json`)
  - UI / orchestration: `src/ui/app_streamlit.py`, `src/plantguard_bot.py`, Streamlit-based apps in `scripts/` (model switcher)
  - Training / data: `src/training/dataset_manager.py`, `scripts/prepare_dataset*.py`, data under `data/processed/plantvillage`

## Immediate developer workflows (commands you should run)
- Setup environment and deps: `make setup` (creates venv and installs everything).
- Launch main app: `make run` (Streamlit on http://localhost:8501).
- Launch model switcher UI: `make switcher` (Streamlit on http://localhost:8502).
- Run tests: `make test` or use the workspace test task (pytest runs `tests/` with coverage).
- Validate project health: `make status` and `make validate-dataset` for dataset checks.

If automating, prefer the Makefile targets rather than calling lower-level scripts directly.

## Project-specific conventions & patterns
- Package layout: code lives in `src/` and is imported as a package; tests live in `tests/`.
- Config-first design: `config/models.json` is authoritative for available models, default, and thresholds — update it when adding models.
- Hot-swap pattern: model switching is handled by `PlantGuardModelManager` in `src/core/model_manager.py` and exposes `switch_model(name)` and `get_readable_prediction(image)` — use these APIs for model changes in code.
- Streamlit caching: model loaders and heavy resources use `@st.cache_resource` — ensure changes invalidate or re-create cached resources when switching models.
- Dataset paths: processed dataset expected at `data/processed/plantvillage`; model artifacts stored in `data/models/`.

## Integration points and external deps
- Hugging Face models: loaded via `src/core/huggingface_vision.py` and configured in `config/models.json`; set `HF_TOKEN` in `.env` for private models.
- Kaggle dataset downloads: scripts call Kaggle API; configure `~/.kaggle/kaggle.json` or run `make download-dataset`.
- Streamlit WebRTC for audio: audio pipeline uses `streamlit-webrtc`; microphone access may require an HTTPS tunnel (pycloudflared or ngrok).
- TensorBoard logs: training writes to `runs/` and is viewable via `make monitor-training`.

## Testing and CI notes
- Tests are discovered under `tests/` (pytest). Pytest config lives in `pyproject.toml` / `pytest.ini` and enforces coverage checks. Use `make test` or the VS Code test tasks.
- Tests use markers (`unit`, `integration`, `gpu`, `model`) — pay attention to marker requirements when adding new tests.

## Concrete examples (copyable snippets)
- Switch model from Python (in code or tests):

  manager = PlantGuardModelManager()
  manager.switch_model("vit_best")

- CLI/quick-switch:

  python scripts/model_switching/model_switcher.py --switch vit_best

- Run a quick validation of the dataset:

  make validate-dataset

## Files to inspect for most changes
- `config/models.json` — model metadata and defaults
- `src/core/model_manager.py` — switching logic, prediction wrapper
- `src/core/huggingface_vision.py` — HF model loading/caching
- `src/ui/app_streamlit.py` and `scripts/model_switching/*` — UI behavior and hot-swap UX
- `src/training/dataset_manager.py` — dataset preparation and validation routines

## Code-writing constraints & style hints
- Follow existing project tooling: run `make format` (Ruff) and `make lint` before committing.
- Line length is configured longer than usual (see `pyproject.toml`), prefer existing style.
- Many external packages are ignored by MyPy in this project — prefer runtime checks for third-party behaviors in tests.

## What to avoid
- Don’t change `config/models.json` without updating unit tests or the model switcher UI.
- Avoid adding heavyweight installs to core tests (use markers to isolate slow/integration tests).

## Where to ask for more context
- If behavior depends on real models or the dataset, request access to `data/processed/plantvillage` or an example model in `data/models/`.

---
If anything here is unclear or you want more examples (e.g., typical unit test patterns around model switching), say which section to expand and I will iterate.
