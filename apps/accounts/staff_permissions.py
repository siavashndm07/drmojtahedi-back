from __future__ import annotations

from django.contrib.auth import get_user_model

User = get_user_model()

STAFF_PERMISSION_KEYS: tuple[str, ...] = (
    "dashboard",
    "content",
    "heritage",
    "archive",
    "foundation",
    "engagement",
    "settings",
)

STAFF_PERMISSION_LABELS: dict[str, str] = {
    "dashboard": "داشبورد",
    "content": "محتوا (اخبار، مقالات، کتاب)",
    "heritage": "میراث (افراد، مکان، خط زمان)",
    "archive": "آرشیو و تاریخ شفاهی",
    "foundation": "بنیاد (پروژه، حامی، ارکان)",
    "engagement": "همراهی (کمک، عضو، خبرنامه)",
    "settings": "تنظیمات و کاربران پنل",
}


def normalize_permissions(raw) -> list[str]:
    if not isinstance(raw, list):
        return []
    allowed = set(STAFF_PERMISSION_KEYS)
    out: list[str] = []
    for item in raw:
        key = str(item).strip()
        if key in allowed and key not in out:
            out.append(key)
    return out


def permissions_for_django_user(user) -> list[str]:
    if user is None:
        return []
    if getattr(user, "is_superuser", False):
        return list(STAFF_PERMISSION_KEYS)
    profile = getattr(user, "staff_profile", None)
    if profile is None:
        return list(STAFF_PERMISSION_KEYS)
    return normalize_permissions(profile.permissions)


def user_has_permission(user, key: str) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return key in permissions_for_django_user(user)


def permission_for_path(path: str) -> str | None:
    p = path.split("?")[0].rstrip("/") or "/"
    if p == "/login" or p.startswith("/account"):
        return None
    if p == "/" or p == "":
        return "dashboard"
    if (
        p.startswith("/news")
        or p.startswith("/articles")
        or p.startswith("/books")
        or p.startswith("/sliders")
    ):
        return "content"
    if p.startswith("/people") or p.startswith("/places") or p.startswith("/timeline"):
        return "heritage"
    if (
        p.startswith("/archive")
        or p.startswith("/oral-history")
        or p.startswith("/media")
        or p.startswith("/galleries")
    ):
        return "archive"
    if (
        p.startswith("/projects")
        or p.startswith("/sponsors")
        or p.startswith("/organs")
        or p.startswith("/useful-links")
    ):
        return "foundation"
    if (
        p.startswith("/donations")
        or p.startswith("/donation-goals")
        or p.startswith("/members")
        or p.startswith("/membership-tiers")
        or p.startswith("/membership-fees")
        or p.startswith("/newsletter")
        or p.startswith("/contributions")
    ):
        return "engagement"
    if p.startswith("/settings") or p.startswith("/ai"):
        return "settings"
    return "dashboard"
