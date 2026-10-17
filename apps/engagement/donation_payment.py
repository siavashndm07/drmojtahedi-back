"""Donate payment start helpers (Zarinpal / Zibal online redirect)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from django.conf import settings

from apps.foundation.gateway_services import (
    GATEWAY_LABELS,
    credentials_for,
    resolve_gateway,
)
from apps.foundation.models import OpsSettings

ZARINPAL = {
    True: {
        "request": "https://sandbox.zarinpal.com/pg/v4/payment/request.json",
        "start": "https://sandbox.zarinpal.com/pg/StartPay/{authority}",
    },
    False: {
        "request": "https://api.zarinpal.com/pg/v4/payment/request.json",
        "start": "https://api.zarinpal.com/pg/StartPay/{authority}",
    },
}

ZIBAL = {
    True: {
        "request": "https://sandbox.zibal.ir/v1/request",
        "start": "https://sandbox.zibal.ir/start/{trackId}",
    },
    False: {
        "request": "https://gateway.zibal.ir/v1/request",
        "start": "https://gateway.zibal.ir/start/{trackId}",
    },
}


def _post_json(url: str, payload: dict, *, timeout: int = 25) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            data = {}
        message = (
            data.get("message")
            or data.get("errors")
            or raw
            or f"HTTP {exc.code}"
        )
        raise ValueError(f"خطا در ارتباط با درگاه: {message}") from exc
    except urllib.error.URLError as exc:
        raise ValueError("ارتباط با درگاه پرداخت برقرار نشد.") from exc

    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise ValueError("پاسخ نامعتبر از درگاه پرداخت.") from exc


def callback_url_for(
    reference_id: int,
    *,
    path: str = "/donate/callback",
    query_key: str = "donation",
) -> str:
    site = getattr(settings, "PUBLIC_SITE_URL", "") or "http://localhost:3000"
    return f"{site.rstrip('/')}{path}?{query_key}={reference_id}"


def start_zarinpal(
    ops: OpsSettings,
    *,
    amount: int,
    description: str,
    donation_id: int,
    callback_path: str = "/donate/callback",
    callback_query_key: str = "donation",
) -> tuple[str, str]:
    creds = credentials_for(ops, OpsSettings.Gateway.ZARINPAL)
    if not creds.merchant_id:
        raise ValueError("Merchant ID زرین‌پال تنظیم نشده است.")
    urls = ZARINPAL[bool(creds.sandbox)]
    data = _post_json(
        urls["request"],
        {
            "merchant_id": creds.merchant_id,
            "amount": int(amount),
            "callback_url": callback_url_for(
                donation_id, path=callback_path, query_key=callback_query_key
            ),
            "description": description[:240] or "کمک بلاعوض",
        },
    )
    errors = data.get("errors")
    if errors:
        raise ValueError(f"زرین‌پال: {errors}")
    result = data.get("data") or {}
    authority = str(result.get("authority") or "").strip()
    code = result.get("code")
    if code not in (100, "100") or not authority:
        raise ValueError("زرین‌پال درخواست پرداخت را نپذیرفت.")
    return authority, urls["start"].format(authority=authority)


def start_zibal(
    ops: OpsSettings,
    *,
    amount: int,
    description: str,
    donation_id: int,
    callback_path: str = "/donate/callback",
    callback_query_key: str = "donation",
) -> tuple[str, str]:
    creds = credentials_for(ops, OpsSettings.Gateway.ZIBAL)
    if not creds.merchant_id:
        raise ValueError("Merchant ID زیبال تنظیم نشده است.")
    urls = ZIBAL[bool(creds.sandbox)]
    data = _post_json(
        urls["request"],
        {
            "merchant": creds.merchant_id,
            "amount": int(amount),
            "callbackUrl": callback_url_for(
                donation_id, path=callback_path, query_key=callback_query_key
            ),
            "description": description[:240] or "کمک بلاعوض",
        },
    )
    result = int(data.get("result") or 0)
    track_id = data.get("trackId")
    if result != 100 or track_id is None:
        message = data.get("message") or "زیبال درخواست پرداخت را نپذیرفت."
        raise ValueError(str(message))
    track = str(track_id)
    return track, urls["start"].format(trackId=track)


def initiate_donation_payment(
    ops: OpsSettings,
    *,
    amount: int,
    description: str,
    donation_id: int,
    gateway: str | None = None,
    callback_path: str = "/donate/callback",
    callback_query_key: str = "donation",
) -> tuple[str, str, str]:
    """
    Returns (gateway_id, authority, redirect_url).
    """
    resolved = resolve_gateway(ops, gateway)
    label = GATEWAY_LABELS.get(resolved, resolved)
    cb = dict(callback_path=callback_path, callback_query_key=callback_query_key)

    if resolved == OpsSettings.Gateway.ZARINPAL:
        authority, url = start_zarinpal(
            ops,
            amount=amount,
            description=description,
            donation_id=donation_id,
            **cb,
        )
        return resolved, authority, url

    if resolved == OpsSettings.Gateway.ZIBAL:
        authority, url = start_zibal(
            ops,
            amount=amount,
            description=description,
            donation_id=donation_id,
            **cb,
        )
        return resolved, authority, url

    raise ValueError(
        f"هدایت آنلاین برای درگاه «{label}» هنوز پیاده‌سازی نشده است. "
        "از زرین‌پال، زیبال یا کارت‌به‌کارت استفاده کنید."
    )
