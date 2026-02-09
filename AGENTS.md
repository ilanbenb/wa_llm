# Repository Guidelines

## Project Structure & Module Organization
- Source code: `src/` — key packages: `api/`, `handler/`, `models/`, `whatsapp/`, `utils/`, `config/`.
- Application entrypoint: `app/main.py` (starts FastAPI, wiring DB, WhatsApp client).
- Migrations: `migrations/` with `alembic.ini`.
- Tests are colocated with code: `src/**/test_*.py` (e.g., `src/whatsapp/test_jid.py`).
- Extras: `notebooks/`, `data/`.

## Build, Test, and Development Commands
- Install deps: `uv sync --all-extras --active` (Python 3.14).
- Lint/format: `ruff check` and `ruff format`.
- Type check: `pyright`.
- Run tests: `pytest -q` or `pytest --cov=src --cov-report=xml`.
- Run API locally: `uv run python app/main.py` (reads `.env` in repo root). Alt: `uvicorn app.main:app --reload`.
- Docker stack: `docker compose up -d` (services: `postgres`, `whatsapp`, `web-server`).

## Coding Style & Naming Conventions
- Python style: 4‑space indent, f-strings, type hints for public functions, absolute imports from `src` (e.g., `from handler.router import Router`).
- Naming: modules/functions `snake_case`; classes `CamelCase`; constants `UPPER_CASE`.
- Keep functions small and async-friendly where I/O is involved.
- Enforce with `ruff` (style/format) and `pyright` (types) before committing.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Test files: `test_*.py` next to modules (e.g., `src/handler/test_router.py`).
- Use `AsyncMock`/fixtures (see `src/test_utils/`) and avoid real network/DB calls.
- Coverage: `pytest --cov=src` (XML written to `coverage.xml`).

## Commit & Pull Request Guidelines
- Use Conventional Commits when possible: `feat:`, `fix:`, `chore:`, etc. Example: `fix: avoid quote reply loop`.
- PRs must include: clear description, linked issues, validation steps, and notes on DB migrations if applicable. Attach logs/screenshots where useful.
- Gating: ensure `ruff`, `pyright`, and `pytest` pass locally.

## Security & Configuration Tips
- Secrets live in `.env` (root). Required keys include: `DB_URI`, `WHATSAPP_HOST`, `VOYAGE_API_KEY`, `ANTHROPIC_API_KEY`, `LOGFIRE_TOKEN`.
- DB migrations: `alembic upgrade head`; create new migration with `alembic revision --autogenerate -m "<msg>"`.
