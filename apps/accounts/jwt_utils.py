from datetime import datetime, timedelta, timezone
import jwt
from django.conf import settings


def _encode(payload: dict, expires_in: timedelta) -> str:
    data = {
        **payload,
        "exp": datetime.now(timezone.utc) + expires_in,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(data, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])


def issue_access(subject: str, kind: str, **extra) -> str:
    return _encode(
        {"sub": subject, "kind": kind, **extra},
        timedelta(minutes=settings.JWT_ACCESS_MINUTES),
    )


def issue_refresh(subject: str, kind: str) -> str:
    return _encode(
        {"sub": subject, "kind": kind, "typ": "refresh"},
        timedelta(days=settings.JWT_REFRESH_DAYS),
    )
