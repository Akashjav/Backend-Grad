"""Deliver the private transactional outbox through configured SMTP.

Run as a single worker. Failed messages remain queued; bodies are cleared after delivery.
"""

import asyncio
import os
import smtplib
import ssl
import argparse
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.platform import MailOutbox


def send(row):
    message = EmailMessage()
    message["From"] = os.environ["SMTP_FROM"]
    message["To"] = row.recipient
    message["Subject"] = row.subject
    message.set_content(row.body)
    port = int(os.getenv("SMTP_PORT", "587"))
    context = ssl.create_default_context()
    connection = smtplib.SMTP_SSL(os.environ["SMTP_HOST"], port, timeout=20, context=context) if port == 465 else smtplib.SMTP(os.environ["SMTP_HOST"], port, timeout=20)
    with connection as smtp:
        if port != 465:
            smtp.starttls(context=context)
        if os.getenv("SMTP_USERNAME"):
            smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
        smtp.send_message(message)


async def deliver_batch():
    delivered = 0
    for _ in range(100):
        async with AsyncSessionLocal() as db:
            row = (await db.scalars(select(MailOutbox).where(MailOutbox.sent_at.is_(None))
                .order_by(MailOutbox.id).limit(1).with_for_update(skip_locked=True))).first()
            if row is None:
                break
            await asyncio.to_thread(send, row)
            row.sent_at = datetime.utcnow()
            row.body = "[delivered]"
            await db.commit()
            delivered += 1
    return delivered


async def main(loop=False):
    if not os.getenv("SMTP_HOST") or not os.getenv("SMTP_FROM"):
        raise SystemExit("Configure SMTP_HOST and SMTP_FROM before sending mail")
    while True:
        try:
            count = await deliver_batch()
            print(f"Delivered {count} queued messages", flush=True)
        except Exception as exc:
            print(f"Mail delivery failed: {type(exc).__name__}; pending messages retained", flush=True)
            if not loop:
                raise SystemExit(1)
        if not loop:
            break
        await asyncio.sleep(10)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    asyncio.run(main(parser.parse_args().loop))
