import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.tokens import jwt
from sqlalchemy import select, update
from app.core.config import settings
from app.core.security import verify_password
from app.models.user import User
from app.models.profile import Profile
from app.models.student import StudentProfile
from app.models.alumni import AlumniProfile
from app.models.platform import (
    AuthSession,
    AuthChallenge,
    MailOutbox,
    DomainProfile,
    Discipline,
)
from app.models.subscription import Domain
from app.core.workers import password_work
from app.repositories.platform import get, add, public, audit


def password_hash(password):
    salt = secrets.token_hex(16)
    value = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return f"scrypt${salt}${value}"


def password_valid(password, encoded):
    if not encoded.startswith("scrypt$"):
        return verify_password(password, encoded)
    _, salt, expected = encoded.split("$")
    actual = hashlib.scrypt(
        password.encode(), salt=salt.encode(), n=16384, r=8, p=1
    ).hex()
    return hmac.compare_digest(expected, actual)


def digest(value):
    return hmac.new(
        settings.JWT_SECRET_KEY.encode(), value.encode(), hashlib.sha256
    ).hexdigest()


async def validate_domain(db, domain_id, discipline_id):
    if domain_id is not None:
        await get(db, Domain, domain_id)
    if discipline_id is not None:
        discipline = await get(db, Discipline, discipline_id)
        if discipline.domain_id != domain_id:
            raise HTTPException(
                422, "Discipline does not belong to the selected domain"
            )


async def issue_session(db, user):
    refresh = secrets.token_urlsafe(48)
    session = await add(
        db,
        AuthSession,
        id=secrets.token_hex(24),
        user_id=user.id,
        token_hash=digest(refresh),
        expires_at=datetime.utcnow() + timedelta(days=14),
    )
    token = jwt.encode(
        {
            "sub": user.id,
            "sid": session.id,
            "type": "access",
            "exp": datetime.utcnow()
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    return {
        "access_token": token,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


async def challenge(db, user, purpose):
    await db.execute(
        update(AuthChallenge)
        .where(AuthChallenge.user_id == user.id, AuthChallenge.purpose == purpose)
        .values(used=True)
    )
    code = (
        str(secrets.randbelow(900000) + 100000)
        if purpose == "verify"
        else secrets.token_urlsafe(32)
    )
    await add(
        db,
        AuthChallenge,
        user_id=user.id,
        purpose=purpose,
        token_hash=digest(code),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    await add(
        db,
        MailOutbox,
        recipient=user.email,
        subject=f"GradAlumni {purpose}",
        body=f"Your {purpose} code: {code}\nExpires in 15 minutes.",
    )


async def consume_challenge(db, email, code, purpose):
    user = (await db.scalars(select(User).where(User.email == email.lower()))).first()
    row = None
    if user:
        row = (
            await db.scalars(
                select(AuthChallenge)
                .where(
                    AuthChallenge.user_id == user.id,
                    AuthChallenge.purpose == purpose,
                    AuthChallenge.used.is_(False),
                )
                .order_by(AuthChallenge.id.desc())
                .with_for_update()
            )
        ).first()
    if not row or row.expires_at <= datetime.utcnow() or row.attempts >= 5:
        raise HTTPException(400, "Invalid or expired code")
    row.attempts += 1
    if not hmac.compare_digest(row.token_hash, digest(code)):
        # Persist failed attempts even though the HTTP request fails.
        await db.commit()
        raise HTTPException(400, "Invalid or expired code")
    row.used = True
    return user


async def signup(db, data):
    await validate_domain(db, data.domain_id, data.discipline_id)
    if (await db.scalars(select(User).where(User.email == data.email.lower()))).first():
        raise HTTPException(409, "Email already registered")
    user = await add(
        db,
        User,
        email=data.email.lower(),
        password_hash=await password_work(password_hash, data.password),
        role=data.role,
    )
    await add(db, Profile, user_id=user.id, display_name=data.display_name)
    await add(
        db,
        DomainProfile,
        user_id=user.id,
        domain_id=data.domain_id,
        discipline_id=data.discipline_id,
    )
    if data.role == "student":
        await add(db, StudentProfile, user_id=user.id)
    elif data.role == "alumni":
        await add(db, AlumniProfile, user_id=user.id)
    await challenge(db, user, "verify")
    audit(db, user, "identity.signup", user.id)
    return {
        "user_id": user.id,
        "message": "Account created. Verification email queued.",
    }


async def me(db, user):
    profile = (
        await db.scalars(select(Profile).where(Profile.user_id == user.id))
    ).first()
    domain = await db.get(DomainProfile, user.id)
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_verified": user.is_verified,
        "display_name": profile.display_name if profile else None,
        "profile": public(domain) if domain else None,
    }


async def update_profile(db, user, data):
    row = await db.get(DomainProfile, user.id)
    if not row:
        row = await add(db, DomainProfile, user_id=user.id)
    values = data.model_dump(exclude_unset=True)
    if any(k in values and values[k] != getattr(row, k) for k in ("domain_id", "discipline_id", "organization_name")):
        row.verified = False
    if "domain_id" in values or "discipline_id" in values:
        await validate_domain(
            db,
            values.get("domain_id", row.domain_id),
            values.get("discipline_id", row.discipline_id),
        )
    name = values.pop("display_name", None)
    if name:
        profile = (
            await db.scalars(select(Profile).where(Profile.user_id == user.id))
        ).first()
        if profile:
            profile.display_name = name
    for key, value in values.items():
        if value is not None or key == "discipline_id":
            setattr(row, key, value)
    audit(db, user, "profile.update", user.id)
    await db.flush()
    return await me(db, user)
