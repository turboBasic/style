default:
    @just --list

sync:
    uv sync
    npm install

fmt:
    uv run ruff format .
    uv run ruff check --fix .

lint:
    prek run --all-files

test *args:
    uv run pytest {{ args }}
