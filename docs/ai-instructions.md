# AI instructions

## What this is

`style` is a command-line tool built with Typer. It helps match a person's face with
glasses frames.

## Tooling

`just` fronts everything (`just` lists recipes); `mise` pins the toolchain; `uv` manages
the environment; `prek` runs ruff, pyright (strict) and cspell.

- Use the `just` recipe over invoking a tool; where none fits, `uv run <tool>`.
- Never call ruff or pyright directly for linting; go through `just lint` / `prek`.
- Fix lint errors immediately. Never disable a rule to pass a run; if one must go, turn it
  off in the tool's config with the reason and report it. Unknown words go in the cspell
  config, not a disabled hook.
- Run targeted tests for what changed, not the full suite on every edit.

## Code style

- Validate untrusted input at the boundary with pydantic; keep core types plain.
- No comments unless the why is non-obvious; no docstrings.

## Architecture

Ports and adapters with one composition root (`main.py`).

- The CLI depends on a use-case Protocol, never on a concrete service.
- Use cases depend on a library Protocol (the port), never on `osxphotos`.
- `osxphotos` is touched only in its adapter, loaded dynamically and typed through local
  Protocols so pyright strict passes. Keep it that way.

## Testing

Fakes implement the Protocols; tests never touch the real Photos library.

## Not source

`resources/faces` holds person's photos, `resources/frames` holds photos of glasses' frames.
