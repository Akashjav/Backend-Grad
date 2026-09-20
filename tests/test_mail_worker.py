import pytest
from sqlalchemy import select
from app.models.platform import MailOutbox
from scripts import deliver_mail


async def test_successful_mail_is_committed_before_later_failure(env, monkeypatch):
    _, factory, _, _, _ = env
    monkeypatch.setattr(deliver_mail, "AsyncSessionLocal", factory)
    async with factory() as db:
        db.add_all([MailOutbox(recipient="test@example.invalid", subject="Test", body=str(i)) for i in range(2)])
        await db.commit()
    sent = []
    def fake_send(row):
        if sent:
            raise ConnectionError("SMTP unavailable")
        sent.append(row.id)
    monkeypatch.setattr(deliver_mail, "send", fake_send)
    with pytest.raises(ConnectionError):
        await deliver_mail.deliver_batch()
    async with factory() as db:
        rows = list((await db.scalars(select(MailOutbox).order_by(MailOutbox.id))).all())
        assert rows[0].sent_at is not None and rows[0].body == "[delivered]"
        assert rows[1].sent_at is None and rows[1].body == "1"
