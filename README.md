![CI](https://github.com/Razaroth/game-project/actions/workflows/ci.yml/badge.svg?branch=main)

## Quick Setup (Windows)
- **Python:** Install Python 3.11 or 3.12.
- **Create venv:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

- **Install deps:**

```powershell
pip install -r requirements.txt
```

- **Run web UI:**

```powershell
python webui.py
```

- **Open UI:** Visit http://localhost:5000 and log in or register.

### VS Code Tasks
- Open this folder in VS Code.
- Run `Install requirements` to install dependencies.
- Run `Run web UI` to start the web server.
- (Optional) Run `Run game server` if you want a separate game backend.

## Notes
- Accounts persist in `data/accounts.json`. Rooms are in `data/rooms.json`.
- The map shows your current room with a pulsing X.
- To stop the server: Ctrl+C in the terminal.
 - On Render, persistence is enabled via a disk. The blueprint mounts a 1GB disk at the project root so `data/` survives restarts and deploys.

## Copilot Checklist
- Verified `.github/copilot-instructions.md` exists with project tasks.

# Python MUD MMORPG (Cyberpunk Web Edition)

This project is a cyberpunk-themed, text-based MMORPG with a modern web UI. It features real-time multiplayer, graphical map, and advanced character customization.

## Features
- User authentication (registration, login, password hashing)
- Email verification
- Admin tools
- Custom races and classes
- Health and inventory display
- Mobile-friendly, cyberpunk UI
- Matrix rain background effect
- Graphical map/grid of rooms
- Real-time updates via SocketIO
- XP and Level progression persists per account
- Equipment system with slots and UI panel

## Getting Started

### Requirements
- Python 3.11–3.12 recommended
   - Note: Python 3.14 is very new and some dependencies (websocket/async backends) may not yet fully support it on Windows.

### Setup
1. Clone or download this repository.
2. (Optional) Create and activate a virtual environment:
   ```pwsh
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. (Optional) Create a .env file (for secrets like mail):
   ```pwsh
   Copy-Item .env.example .env
   # Edit .env with your values
   ```
4. Install dependencies:
   ```pwsh
   pip install -r requirements.txt
   ```
   - Optional for better Socket.IO performance (if you encounter long-polling):
   ```pwsh
   pip install eventlet
   ```
5. Run the web UI server:
   ```pwsh
   python webui.py
   ```
6. Open your browser and navigate to `http://localhost:5000`

## Project Structure
- `server.py` - Main server entry point
- `game/` - Game logic (world, player, commands)
- `web/` - Web UI (templates, static files)
- `.github/copilot-instructions.md` - Copilot automation instructions
 - `.github/workflows/ci.yml` - GitHub Actions CI (syntax check + optional lint)
 - `.github/ISSUE_TEMPLATE/` - Bug/feature templates
 - `.github/PULL_REQUEST_TEMPLATE.md` - PR checklist

## Contributing
- Fork the repo and submit pull requests
- Follow PEP8 and best practices
 - See CONTRIBUTING.md for details

## License
MIT

## Expanding the Game
- Add new commands in `game/commands.py`
- Equip/Unequip: Use `equip <item>` and `unequip <slot>`; the equipment panel updates in the top-left UI under the map.
- Expand the world in `data/rooms.json` or similar
- Add player/NPC logic in `game/player.py` and `game/npc.py`

## Notes on Progression Persistence
- Accounts store `xp`, `level`, and `xp_max`. On connect, the server restores these values. After each command, updated values are saved to `data/accounts.json`.
- Level and XP are displayed in the Player panel. Level appears under Class.

---
This is a starting point. Expand and customize as you wish!