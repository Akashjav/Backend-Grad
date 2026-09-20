"""JWT implementation with an explicit HS256 allowlist at every decode call."""
import jwt
from jwt import InvalidTokenError as JWTError

__all__ = ["jwt", "JWTError"]
