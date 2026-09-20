"""Read-only preflight; never prints credentials or modifies the database."""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv()


async def check(connect=False):
    url = os.getenv("DATABASE_URL", "")
    parsed = urlsplit(url)
    origins = [v.strip() for v in os.getenv("CORS_ORIGINS", "").split(",") if v.strip()]
    result = {
        "environment": os.getenv("APP_ENV", "development"),
        "database_configured": bool(url),
        "database_remote": parsed.hostname not in {None, "localhost", "127.0.0.1"},
        "database_tls_requested": "sslmode=" in parsed.query or "ssl=" in parsed.query,
        "jwt_length_at_least_32": len(os.getenv("JWT_SECRET_KEY", "")) >= 32,
        "cors_all_https": bool(origins) and all(o.startswith("https://") and "*" not in o for o in origins),
        "allowed_hosts_configured": bool(os.getenv("ALLOWED_HOSTS")),
        "redis_configured": bool(os.getenv("REDIS_URL")),
        "smtp_configured": all(os.getenv(k) for k in ["SMTP_HOST", "SMTP_FROM"]),
        "document_path_configured": bool(os.getenv("DOCUMENT_STORAGE_PATH")),
    }
    if connect:
        from app.db.session import engine
        from sqlalchemy import text
        try:
            async with asyncio.timeout(15):
                async with engine.connect() as connection:
                    await connection.execute(text("SET TRANSACTION READ ONLY"))
                    await connection.execute(text("SELECT 1"))
                    version = (await connection.execute(text("SELECT version_num FROM alembic_version"))).scalar()
                    result["database_reachable"] = True
                    result["migration_revision"] = version
        except Exception as exc:
            result["database_reachable"] = False
            result["connection_error_type"] = type(exc).__name__
        finally:
            await engine.dispose()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--connect", action="store_true", help="Run read-only DB connectivity/schema query")
    asyncio.run(check(parser.parse_args().connect))
