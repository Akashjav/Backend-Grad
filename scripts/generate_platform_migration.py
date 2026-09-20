"""Development utility: freeze new table DDL into a reviewed Alembic revision."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from alembic.autogenerate import render_python_code
from alembic.operations import ops
from app.db import base  # noqa: F401 - register foundation tables for foreign keys
from app.models.user import Base
from app.models import platform

names = {
    value.__table__.name
    for value in vars(platform).values()
    if isinstance(value, type) and hasattr(value, "__table__")
}
tables = [table for table in Base.metadata.sorted_tables if table.name in names]
upgrade_ops = []
for table in tables:
    upgrade_ops.append(ops.CreateTableOp.from_table(table))
    upgrade_ops.extend(
        ops.CreateIndexOp.from_index(index)
        for index in sorted(table.indexes, key=lambda i: i.name)
    )
upgrade = render_python_code(ops.UpgradeOps(upgrade_ops))
downgrade = render_python_code(
    ops.DowngradeOps([ops.DropTableOp.from_table(table) for table in reversed(tables)])
)
target = Path("alembic/versions/ga20_platform.py")
if target.exists():
    raise SystemExit("Refusing to overwrite an existing migration")
target.write_text(
    '''"""Add GradAlumni 2.0 competency and collaboration modules."""
from alembic import op
import sqlalchemy as sa

revision = "ga20_platform"
down_revision = "cf41663d3341"
branch_labels = None
depends_on = None


def upgrade():
'''
    + upgrade
    + "\n\n\ndef downgrade():\n"
    + downgrade
    + "\n",
    encoding="utf-8",
)
print(f"Created {target} with {len(tables)} new tables")
