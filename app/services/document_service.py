import io
import os
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException
from pypdf import PdfReader
from app.core.workers import document_work

MAX_BYTES = 5 * 1024 * 1024


def storage_root():
    return Path(os.getenv("DOCUMENT_STORAGE_PATH", "uploads/private")).resolve()


async def read_pdf(file):
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Maximum document size is 5 MiB")
    if not data.startswith(b"%PDF-") or not (file.filename or "").lower().endswith(
        ".pdf"
    ):
        raise HTTPException(415, "A PDF document is required")
    return data, await document_work(extract_text, data)


def extract_text(data):
    try:
        pdf = PdfReader(io.BytesIO(data))
        if pdf.is_encrypted or len(pdf.pages) > 20:
            raise ValueError("Encrypted PDF or too many pages")
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if len(text) > 100000:
            raise ValueError("Extracted text too large")
    except Exception:
        raise HTTPException(
            422, "Cannot parse PDF; use an unencrypted text PDF of at most 20 pages"
        )
    return text


def save(data, extension=".pdf"):
    root = storage_root()
    root.mkdir(parents=True, exist_ok=True)
    name = uuid4().hex + extension
    (root / name).write_bytes(data)
    return name


def path_for(name):
    root = storage_root()
    path = (root / name).resolve()
    if path.parent != root:
        raise HTTPException(400, "Invalid document path")
    return path
