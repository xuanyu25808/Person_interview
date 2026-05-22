# Backend

This backend uses `uv` for environment management and command execution.

## Setup

```bash
uv sync --directory backend
```

## Start the API

```bash
uv run --directory backend uvicorn app.main:app --app-dir src --reload
```

## Run tests

```bash
uv run --directory backend pytest
```
