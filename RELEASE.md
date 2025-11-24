# Release Branch

This is the **release** branch for MineCompanionAI-WebUI v0.5.0-beta.

## Purpose

This branch contains **ONLY** production-ready code:
- Compiled frontend (`frontend/dist/`)
- Backend Python code (`api/`, `core/`, `main.py`, etc.)
- Configuration templates
- Documentation for deployment

**Frontend source code is excluded** - only the compiled output is included.

## Workflow

1. Develop on `develop/0.5.0-beta` branch
2. When ready to release:
   ```bash
   # Compile frontend
   npm run build

   # Switch to release branch
   git checkout release

   # Copy compiled output
   # (automated script TBD)

   # Commit and push
   git commit -m "chore: release v0.5.0-beta"
   git push origin release:main
   ```

3. Remote `main` branch receives production-ready code

## Structure

```
MineCompanionAI-WebUI/ (release branch)
├── frontend/
│   └── dist/          # Compiled React app ✓
│   (src/ excluded)    # Source code ✗
├── api/               # FastAPI routes ✓
├── core/              # Business logic ✓
├── config/            # Configuration ✓
├── main.py            # Entry point ✓
├── pyproject.toml     # Python deps ✓
└── README.md          # User documentation ✓
```

## Deployment

Users who clone from remote `main` can run:
```bash
# Install Python dependencies
uv sync

# Run backend (frontend already compiled)
uv run python main.py
```

No need to install Node.js or build frontend.

---

**Note**: This branch should **NOT** be used for development. Always develop on `develop/0.5.0-beta` branch.
