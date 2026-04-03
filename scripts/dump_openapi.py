#!/usr/bin/env python3
"""Extract OpenAPI spec from the FastAPI app without requiring a database."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mesh_platform.app import create_app

app = create_app(skip_lifespan=True)
spec = app.openapi()

spec["servers"] = [
    {"url": "https://api.agentmesh.world", "description": "Production"},
    {"url": "http://localhost:8000", "description": "Local development"},
]

out = Path(__file__).resolve().parent.parent / "fern" / "openapi" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(spec, indent=2))
print(f"OpenAPI spec written to {out} ({len(spec.get('paths', {}))} paths)")
