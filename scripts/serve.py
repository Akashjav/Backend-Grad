"""One entrypoint for local, Docker and managed-host production workers."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", "8000")),
        workers=int(os.getenv("WEB_CONCURRENCY", "4")),
        limit_concurrency=int(os.getenv("WORKER_CONCURRENCY", "400")),
        backlog=2048, timeout_keep_alive=5, timeout_graceful_shutdown=30,
        ws_max_size=16384, ws_max_queue=16,
        forwarded_allow_ips=os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1"),
        access_log=False, log_level=os.getenv("LOG_LEVEL", "info"))
