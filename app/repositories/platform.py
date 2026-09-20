"""Shared persistence operations. Transactions are owned by API dependencies."""

from fastapi import HTTPException
from sqlalchemy import select, Uuid
from uuid import UUID
from app.models.platform import AuditLog


async def get(db, model, identity, *, lock=False):
    if isinstance(model.__mapper__.primary_key[0].type, Uuid):
        try:
            identity = str(UUID(str(identity)))
        except (TypeError, ValueError, AttributeError):
            raise HTTPException(422, 'A valid UUID is required')
    statement = select(model).where(model.__mapper__.primary_key[0] == identity)
    if lock:
        statement = statement.with_for_update()
    row = (await db.execute(statement)).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, f"{model.__name__} not found")
    return row


async def rows(db, model, *conditions, limit=100, offset=0):
    return list(
        (
            await db.scalars(
                select(model)
                .where(*conditions)
                .order_by(model.__mapper__.primary_key[0])
                .offset(offset)
                .limit(limit)
            )
        ).all()
    )


async def add(db, model, **values):
    row = model(**values)
    db.add(row)
    await db.flush()
    return row


def public(row, exclude=()):
    return {
        c.name: getattr(row, c.name)
        for c in row.__table__.columns
        if c.name not in exclude
    }


def audit(db, user, action, target, **details):
    db.add(
        AuditLog(actor_id=user.id, action=action, target=str(target), details=details)
    )
