"""Generate the exact executable REST contract and reference coverage report."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app

root = Path("docs")
root.mkdir(exist_ok=True)
schema = app.openapi()
(root / "openapi.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
lines = [
    "# GradAlumni 2.0 API inventory",
    "",
    "Generated from the running FastAPI route definitions. See `openapi.json` for request bodies and schemas.",
    "",
    "| Method | Endpoint | Module |",
    "|---|---|---|",
]
for path, methods in sorted(schema["paths"].items()):
    for method, operation in methods.items():
        lines.append(
            f"| {method.upper()} | `{path}` | {', '.join(operation.get('tags', []))} |"
        )
lines += [
    "",
    "## WebSocket",
    "",
    '`WS /api/v1/ws/conversations/{conversation_id}`: send `{"token":"ACCESS_TOKEN"}` as the first frame within 10 seconds, then `{"body":"message"}`.',
    "",
    "Messages are persisted in PostgreSQL. Other participants receive committed messages through one-second database polling. No in-memory broadcast dependency; Redis pub/sub is a future scaling optimization.",
]
reference = Path("tmp/pdfs/reference.txt")
if reference.exists():
    normalize = lambda p: re.sub(r"\{[^}]+\}", "{}", p.rstrip("/"))
    actual = {
        (m.upper(), normalize(p))
        for p, methods in schema["paths"].items()
        for m in methods
    }
    actual.add(("WS", normalize("/api/v1/ws/conversations/{conversation_id}")))
    expected = set(
        re.findall(
            r"(GET|POST|PATCH|PUT|DELETE|WS)\s+(/api/v1/[^\s]+)",
            reference.read_text(encoding="utf-8"),
        )
    )
    missing = [(m, p) for m, p in expected if (m, normalize(p)) not in actual]
    lines += [
        "",
        "## Earlier API specification coverage",
        "",
        f"{len(expected) - len(missing)} / {len(expected)} distinct method/path targets registered. Path parameter names are normalized for comparison. This is route coverage, not a claim that every route is independently integration-tested.",
    ]
    lines += [f"- Missing: `{m} {p}`" for m, p in missing]
(root / "API_INVENTORY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Exported {len(schema['paths'])} REST paths and WebSocket contract")
