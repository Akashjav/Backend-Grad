from fastapi import HTTPException


def require_role(user, *roles):
    if not user.is_active or user.role not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def check_admin(user):
    require_role(user, "admin", "super_admin")
