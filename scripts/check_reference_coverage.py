"""Compare an extracted earlier API PDF with the executable OpenAPI contract."""
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app

def normalize(path):
    return re.sub(r'\{[^}]+\}', '{}', path.rstrip('/'))

expected = set(re.findall(r'(GET|POST|PATCH|PUT|DELETE|WS)\s+(/api/v1/[^\s]+)', Path('tmp/pdfs/reference.txt').read_text(encoding='utf-8')))
actual = {(method.upper(), normalize(path)) for path, methods in app.openapi()['paths'].items() for method in methods}
actual.add(('WS', normalize('/api/v1/ws/conversations/{conversation_id}')))
missing = [(method, path) for method, path in expected if (method, normalize(path)) not in actual]
assert not missing, missing
print(f'{len(expected)} distinct proposed method/path targets registered')
