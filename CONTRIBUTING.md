# Contributing

Thanks for your interest in contributing! This guide keeps contributions smooth and consistent.

## Getting Started

- Supported Python: 3.11–3.12
- Clone and set up:
  ```pwsh
  git clone https://github.com/Razaroth/game-project.git
  cd game-project
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

## Running Locally

- VS Code tasks:
  - Run `Install requirements`
  - Run `Run web UI`
- Or via terminal:
  ```pwsh
  python webui.py
  ```
  Then open <http://localhost:5000>

## Before You Commit

- Syntax check (required):
  ```pwsh
  python -m compileall -q .
  ```
- Lint (optional but encouraged):
  ```pwsh
  pip install flake8
  flake8 --extend-ignore=E203,W503 --max-line-length=100 .
  ```

## Branch & PR Flow

1. Create a feature branch:
   ```pwsh
   git checkout -b feat/short-description
   ```
2. Commit with clear messages (Conventional style optional):
   - `feat: add cyber grid map`
   - `fix: prevent crash on empty inventory`
3. Push and open a PR:
   ```pwsh
   git push -u origin HEAD
   ```
4. Fill out the PR template and ensure CI is green.

## Where to Contribute

- Game commands: `game/commands.py`
- Player stats/logic: `game/player.py`
- World/rooms: `data/rooms.json`, `game/world.py`
- Web UI: `web/templates/`, `web/static/`

## Reporting Issues

Use the issue templates:

- Bug reports → Issues → New issue → Bug report
- Feature ideas → Issues → New issue → Feature request

## Code Style

- Prefer readable, small functions
- Keep changes focused; avoid unrelated refactors
- Follow project structure and existing patterns

Thanks for helping improve the project!
