# Repository Guidelines

## Project Structure & Module Organization
- `README.md`: Product vision and end-to-end workflow for the research copilot.
- `readme_spoonOS.md`: Implementation notes for wiring the copilot on SpoonOS plus toolkit/LLM/graph references.
- `main.py`: Simple CLI banner bootstrapper.
- `spoon-core/`: SpoonOS core (agents, LLM manager, graph system, docs, examples).
- `spoon-toolkit/`: Tool collection (data/search, crypto, storage, social, GitHub). See its `README.md` for per-tool env vars.
- `spoon-env/`: Python venv (activate before development).

## Build, Test, and Development Commands
- Activate env: `source spoon-env/bin/activate`
- Install deps (core + toolkit): `pip install -r spoon-core/requirements.txt && pip install -r spoon-toolkit/requirements.txt`
- Lint/format (if configured): use `ruff`/`black` if present in your toolchain; otherwise follow PEP 8 manually.
- Tests: none shipped; add targeted tests to `spoon-core/tests/` when introducing logic changes.

## Coding Style & Naming Conventions
- Python 3.11+; follow PEP 8 (4-space indent, snake_case for functions/vars, PascalCase for classes).
- Keep modules cohesive: core framework code in `spoon_core`, toolkit additions in `spoon_toolkits`.
- Add short, meaningful docstrings and type hints; avoid non-ASCII unless already present.
- Configuration: prefer environment variables (`.env`) over hardcoded secrets; never commit keys.

## Testing Guidelines
- When adding behavior, create focused tests under `spoon-core/tests/` mirroring module paths.
- Name tests `test_<module>.py`; prefer pytest-style asserts.
- For tools hitting external APIs, stub/mimic responses; do not rely on live keys in CI.

## Commit & Pull Request Guidelines
- Commits: keep scope small with imperative summaries (e.g., `Add graph node for hypothesis stage`; `Document Spoon toolkit usage`). Include rationale in body if non-trivial.
- Pull requests: describe change, affected modules/paths, and manual/automated checks run. Link issues/tasks when available. Provide screenshots or sample outputs for UX/API changes.

## Security & Configuration Tips
- Required keys are provider-specific (OpenAI/Anthropic/DeepSeek, Chainbase, OKX, social tokens, storage). Place them in `.env`; do not commit.
- If adding new tools/providers, document required env vars in the relevant README and validate presence at runtime. 
