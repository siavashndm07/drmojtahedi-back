from __future__ import annotations

from dataclasses import dataclass

from apps.foundation.models import OpsSettings

CHECKOUT_GATEWAY_IDS = (
    OpsSettings.Gateway.ZARINPAL,
    OpsSettings.Gateway.ZIBAL,
    OpsSettings.Gateway.SEP,
    OpsSettings.Gateway.PASARGAD,
    OpsSettings.Gateway.MELLAT,
    OpsSettings.Gateway.IRANKISH,
)

GATEWAY_LABELS = dict(OpsSettings.Gateway.choices)

DEFAULT_PASARGAD_BASE_URL = "https://pep.shaparak.ir/dorsa1"


def _empty_row(gateway_id: str) -> dict:
    return {
        "enabled": False,
        "sandbox": gateway_id
        not in (OpsSettings.Gateway.SEP, OpsSettings.Gateway.IRANKISH),
        "merchant_id": "",
        "merchant_code": "",
        "username": "",
        "private_key": "",
        "public_key": "",
        "base_url": DEFAULT_PASARGAD_BASE_URL if gateway_id == OpsSettings.Gateway.PASARGAD else "",
    }


def bootstrap_from_legacy(ops: OpsSettings | None) -> dict[str, dict]:
    gateways = {gateway_id: _empty_row(gateway_id) for gateway_id in CHECKOUT_GATEWAY_IDS}
    if not ops:
        return gateways
    legacy = (ops.gateway or "").strip()
    if legacy in CHECKOUT_GATEWAY_IDS and ops.merchant_id.strip():
        row = {
            "enabled": True,
            "sandbox": bool(ops.sandbox),
            "merchant_id": ops.merchant_id.strip(),
            "merchant_code": ops.gateway_merchant_code.strip(),
            "username": "",
            "private_key": ops.gateway_private_key.strip(),
            "public_key": "",
            "base_url": DEFAULT_PASARGAD_BASE_URL if legacy == OpsSettings.Gateway.PASARGAD else "",
        }
        # Older Mellat/Pasargad layouts reused merchant_code as username.
        if legacy == OpsSettings.Gateway.MELLAT:
            row["username"] = ops.gateway_merchant_code.strip()
        gateways[legacy] = row
    return gateways


def normalize_payment_gateways(raw, ops: OpsSettings | None = None) -> dict[str, dict]:
    base = bootstrap_from_legacy(ops)
    if isinstance(raw, dict) and raw:
        for gateway_id in CHECKOUT_GATEWAY_IDS:
            row = raw.get(gateway_id)
            if not isinstance(row, dict):
                continue
            merged = {**base[gateway_id], **row}
            merged["enabled"] = bool(row.get("enabled", merged["enabled"]))
            merged["sandbox"] = bool(row.get("sandbox", merged["sandbox"]))
            merged["merchant_id"] = str(
                row.get("merchant_id") if row.get("merchant_id") is not None else merged["merchant_id"]
            ).strip()
            merged["merchant_code"] = str(
                row.get("merchant_code")
                if row.get("merchant_code") is not None
                else merged["merchant_code"]
            ).strip()
            merged["username"] = str(
                row.get("username") if row.get("username") is not None else merged.get("username", "")
            ).strip()
            merged["private_key"] = str(
                row.get("private_key")
                if row.get("private_key") is not None
                else merged["private_key"]
            ).strip()
            merged["public_key"] = str(
                row.get("public_key")
                if row.get("public_key") is not None
                else merged.get("public_key", "")
            ).strip()
            merged["base_url"] = str(
                row.get("base_url") if row.get("base_url") is not None else merged.get("base_url", "")
            ).strip()
            # Mellat historically stored username in merchant_code.
            if gateway_id == OpsSettings.Gateway.MELLAT and not merged["username"]:
                merged["username"] = merged["merchant_code"]
            if gateway_id == OpsSettings.Gateway.PASARGAD and not merged["base_url"]:
                merged["base_url"] = DEFAULT_PASARGAD_BASE_URL
            base[gateway_id] = merged
    return base


def gateway_row_ready(gateway_id: str, row: dict) -> bool:
    merchant_id = str(row.get("merchant_id") or "").strip()
    if not merchant_id:
        if gateway_id == OpsSettings.Gateway.ZIBAL and row.get("sandbox"):
            return True
        return False
    if gateway_id == OpsSettings.Gateway.PASARGAD:
        username = str(row.get("username") or "").strip()
        password = str(row.get("private_key") or "").strip()
        merchant_code = str(row.get("merchant_code") or "").strip()
        return bool(merchant_id and merchant_code and username and password)
    if gateway_id == OpsSettings.Gateway.MELLAT:
        username = str(row.get("username") or row.get("merchant_code") or "").strip()
        password = str(row.get("private_key") or "").strip()
        return bool(merchant_id and username and password)
    if gateway_id == OpsSettings.Gateway.IRANKISH:
        acceptor_id = str(row.get("merchant_code") or "").strip()
        password = str(row.get("private_key") or "").strip()
        public_key = str(row.get("public_key") or "").strip()
        return bool(merchant_id and acceptor_id and password and public_key)
    return True


def enabled_ready_gateways(ops: OpsSettings | None) -> list[str]:
    if not ops:
        return []
    gateways = normalize_payment_gateways(getattr(ops, "payment_gateways", None), ops)
    ready: list[str] = []
    for gateway_id in CHECKOUT_GATEWAY_IDS:
        row = gateways[gateway_id]
        if row.get("enabled") and gateway_row_ready(gateway_id, row):
            ready.append(gateway_id)
    return ready


def any_gateway_ready(ops: OpsSettings | None) -> bool:
    return bool(enabled_ready_gateways(ops))


def default_gateway(ops: OpsSettings | None) -> str:
    if not ops:
        return OpsSettings.Gateway.NONE
    preferred = (ops.gateway or OpsSettings.Gateway.NONE).strip()
    ready = enabled_ready_gateways(ops)
    if preferred in ready:
        return preferred
    return ready[0] if ready else OpsSettings.Gateway.NONE


def resolve_gateway(ops: OpsSettings | None, requested: str | None = None) -> str:
    ready = enabled_ready_gateways(ops)
    if not ready:
        raise ValueError("درگاه پرداخت فعال نیست.")
    cleaned = (requested or "").strip()
    if cleaned:
        if cleaned not in ready:
            raise ValueError("درگاه انتخاب‌شده فعال نیست.")
        return cleaned
    resolved = default_gateway(ops)
    if resolved not in ready:
        raise ValueError("درگاه پیش‌فرض فعال نیست.")
    return resolved


def get_gateway_row(ops: OpsSettings, gateway_id: str) -> dict:
    gateways = normalize_payment_gateways(getattr(ops, "payment_gateways", None), ops)
    return gateways.get(gateway_id, _empty_row(gateway_id))


@dataclass
class GatewayCredentials:
    gateway_id: str
    sandbox: bool
    merchant_id: str
    merchant_code: str
    username: str
    private_key: str
    base_url: str = ""
    public_key: str = ""


def credentials_for(ops: OpsSettings, gateway_id: str) -> GatewayCredentials:
    row = get_gateway_row(ops, gateway_id)
    username = str(row.get("username") or "").strip()
    merchant_code = str(row.get("merchant_code") or "").strip()
    if gateway_id == OpsSettings.Gateway.MELLAT and not username:
        username = merchant_code
    base_url = str(row.get("base_url") or "").strip()
    if gateway_id == OpsSettings.Gateway.PASARGAD and not base_url:
        base_url = DEFAULT_PASARGAD_BASE_URL
    return GatewayCredentials(
        gateway_id=gateway_id,
        sandbox=bool(row.get("sandbox")),
        merchant_id=str(row.get("merchant_id") or "").strip(),
        merchant_code=merchant_code,
        username=username,
        private_key=str(row.get("private_key") or "").strip(),
        base_url=base_url,
        public_key=str(row.get("public_key") or "").strip(),
    )


def checkout_gateway_options(ops: OpsSettings | None) -> list[dict]:
    if not ops:
        return []
    gateways = normalize_payment_gateways(getattr(ops, "payment_gateways", None), ops)
    options: list[dict] = []
    for gateway_id in CHECKOUT_GATEWAY_IDS:
        row = gateways[gateway_id]
        if not row.get("enabled") or not gateway_row_ready(gateway_id, row):
            continue
        options.append(
            {
                "id": gateway_id,
                "label": GATEWAY_LABELS.get(gateway_id, gateway_id),
                "sandbox": bool(row.get("sandbox")),
            }
        )
    return options


def serialize_payment_gateways_admin(ops: OpsSettings) -> list[dict]:
    gateways = normalize_payment_gateways(getattr(ops, "payment_gateways", None), ops)
    payload: list[dict] = []
    for gateway_id in CHECKOUT_GATEWAY_IDS:
        row = gateways[gateway_id]
        item = {
            "id": gateway_id,
            "label": GATEWAY_LABELS.get(gateway_id, gateway_id),
            "enabled": bool(row.get("enabled")),
            "sandbox": bool(row.get("sandbox")),
            "merchantIdSet": bool(str(row.get("merchant_id") or "").strip()),
            "merchantCode": str(row.get("merchant_code") or ""),
            "usernameSet": bool(str(row.get("username") or "").strip()),
            "privateKeySet": bool(str(row.get("private_key") or "").strip()),
            "publicKeySet": bool(str(row.get("public_key") or "").strip()),
            "baseUrl": str(row.get("base_url") or ""),
        }
        payload.append(item)
    return payload


def merge_payment_gateways_from_admin(
    ops: OpsSettings,
    incoming: list[dict] | None,
    *,
    merchant_ids: dict[str, str] | None = None,
    merchant_codes: dict[str, str] | None = None,
    usernames: dict[str, str] | None = None,
    private_keys: dict[str, str] | None = None,
) -> dict[str, dict]:
    current = normalize_payment_gateways(getattr(ops, "payment_gateways", None), ops)
    merchant_ids = merchant_ids or {}
    merchant_codes = merchant_codes or {}
    usernames = usernames or {}
    private_keys = private_keys or {}

    if not incoming:
        return current

    by_id = {str(item.get("id") or "").strip(): item for item in incoming if isinstance(item, dict)}

    for gateway_id in CHECKOUT_GATEWAY_IDS:
        patch = by_id.get(gateway_id)
        if not patch:
            continue
        row = current[gateway_id]
        if "enabled" in patch:
            row["enabled"] = bool(patch.get("enabled"))
        if "sandbox" in patch:
            row["sandbox"] = bool(patch.get("sandbox"))
        if gateway_id in merchant_ids:
            value = merchant_ids[gateway_id].strip()
            if value:
                row["merchant_id"] = value
        elif patch.get("merchantId"):
            row["merchant_id"] = str(patch.get("merchantId") or "").strip()

        if gateway_id in (
            OpsSettings.Gateway.PASARGAD,
            OpsSettings.Gateway.MELLAT,
            OpsSettings.Gateway.IRANKISH,
        ):
            if gateway_id in merchant_codes:
                value = merchant_codes[gateway_id].strip()
                if value:
                    row["merchant_code"] = value
            elif patch.get("merchantCode") is not None:
                row["merchant_code"] = str(patch.get("merchantCode") or "").strip()

            if gateway_id in usernames:
                value = usernames[gateway_id].strip()
                if value:
                    row["username"] = value
            elif patch.get("username"):
                row["username"] = str(patch.get("username") or "").strip()

            if gateway_id in private_keys:
                value = private_keys[gateway_id].strip()
                if value:
                    row["private_key"] = value
            elif patch.get("privateKey"):
                row["private_key"] = str(patch.get("privateKey") or "").strip()

            if gateway_id == OpsSettings.Gateway.MELLAT and not row.get("username"):
                # Keep Mellat compatible with older admin payloads that only sent merchantCode.
                row["username"] = str(row.get("merchant_code") or "").strip()

            if gateway_id == OpsSettings.Gateway.PASARGAD:
                if patch.get("baseUrl") is not None:
                    base_url = str(patch.get("baseUrl") or "").strip()
                    row["base_url"] = base_url or DEFAULT_PASARGAD_BASE_URL
                elif not row.get("base_url"):
                    row["base_url"] = DEFAULT_PASARGAD_BASE_URL

            if gateway_id == OpsSettings.Gateway.IRANKISH and patch.get("publicKey"):
                row["public_key"] = str(patch.get("publicKey") or "").strip()

        current[gateway_id] = row

    return current


def sync_legacy_flat_fields(ops: OpsSettings) -> None:
    """Keep legacy flat columns aligned with the default gateway row."""
    default = default_gateway(ops)
    if default == OpsSettings.Gateway.NONE:
        return
    row = get_gateway_row(ops, default)
    ops.gateway = default
    ops.sandbox = bool(row.get("sandbox"))
    ops.merchant_id = str(row.get("merchant_id") or "")
    ops.gateway_merchant_code = str(row.get("merchant_code") or "")
    ops.gateway_private_key = str(row.get("private_key") or "")
