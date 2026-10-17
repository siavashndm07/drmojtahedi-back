from __future__ import annotations

import uuid
from collections import deque
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, ImageChops, ImageFilter, ImageOps, UnidentifiedImageError

WEBP_QUALITY = 85
WEBP_MAX_SIDE = 4096

# Per-kind max side (after EXIF fix). Keeps uploads web-sized like Bina.
KIND_MAX_SIDE = {
    "news": 1920,
    "articles": 1920,
    "archive": 2048,
    "people": 1600,
    "sponsors": 1600,
    "hero": 2400,
    "logo": 1024,
    "catalog": 1600,
    "gallery": 2048,
}

MEDIA_KINDS = (
    ("news", "news"),
    ("articles", "articles"),
    ("archive", "archive"),
    ("people", "people"),
    ("sponsors", "sponsors"),
    ("hero", "hero"),
    ("logo", "logo"),
    ("catalog", "catalog"),
    ("gallery", "gallery"),
)

MEDIA_KIND_FOLDERS = {key for key, _ in MEDIA_KINDS}
DEFAULT_MEDIA_KIND = "catalog"

DEFAULT_WATERMARK_KINDS = ("news", "articles", "people", "archive", "hero", "sponsors")
SKIP_WATERMARK_KINDS = frozenset({"logo"})
WATERMARK_POSITIONS = frozenset(
    {"bottom_right", "bottom_left", "top_right", "top_left", "center"}
)


def normalize_media_kind(kind: str | None) -> str:
    value = (kind or DEFAULT_MEDIA_KIND).strip().lower()
    aliases = {
        "article": "articles",
        "sponsor": "sponsors",
        "person": "people",
        "people": "people",
    }
    if value in aliases:
        return aliases[value]
    if value in MEDIA_KIND_FOLDERS:
        return value
    return DEFAULT_MEDIA_KIND


def media_upload_to(instance, filename: str) -> str:
    folder = normalize_media_kind(getattr(instance, "kind", None))
    return f"{folder}/{uuid.uuid4()}.webp"


def _max_side_for_kind(kind: str) -> int:
    return min(WEBP_MAX_SIDE, KIND_MAX_SIDE.get(kind, 1600))


def _site_settings():
    from apps.foundation.models import SiteSettings

    return (
        SiteSettings.objects.select_related("watermark_asset")
        .filter(key="default")
        .first()
    )


def _should_watermark(kind: str, site) -> bool:
    if not site or not site.watermark_enabled or not site.watermark_asset_id:
        return False
    normalized = normalize_media_kind(kind)
    if normalized in SKIP_WATERMARK_KINDS:
        return False
    kinds = site.watermark_apply_kinds or list(DEFAULT_WATERMARK_KINDS)
    return normalized in kinds


def _load_watermark_image(site) -> Image.Image | None:
    asset = getattr(site, "watermark_asset", None)
    if not asset or not asset.file:
        return None
    try:
        with asset.file.open("rb") as handle:
            watermark = Image.open(handle)
            watermark.load()
            return watermark.convert("RGBA")
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def _paste_watermark(
    base: Image.Image,
    watermark: Image.Image,
    *,
    position: str,
    opacity: float,
) -> Image.Image:
    if base.mode != "RGBA":
        base = base.convert("RGBA")

    max_width = max(1, int(base.width * 0.22))
    ratio = max_width / max(1, watermark.width)
    resized = watermark.resize(
        (max_width, max(1, int(watermark.height * ratio))),
        Image.Resampling.LANCZOS,
    )

    clamped_opacity = max(0.05, min(1.0, opacity))
    if clamped_opacity < 1.0:
        alpha = resized.split()[3]
        alpha = alpha.point(lambda value: int(value * clamped_opacity))
        resized.putalpha(alpha)

    pad = max(8, int(min(base.width, base.height) * 0.02))
    positions = {
        "bottom_right": (
            base.width - resized.width - pad,
            base.height - resized.height - pad,
        ),
        "bottom_left": (pad, base.height - resized.height - pad),
        "top_right": (base.width - resized.width - pad, pad),
        "top_left": (pad, pad),
        "center": (
            (base.width - resized.width) // 2,
            (base.height - resized.height) // 2,
        ),
    }
    xy = positions.get(position, positions["bottom_right"])

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    overlay.paste(resized, xy, resized)
    return Image.alpha_composite(base, overlay)


def _apply_watermark(image: Image.Image, site, kind: str) -> Image.Image:
    if not _should_watermark(kind, site):
        return image
    watermark = _load_watermark_image(site)
    if watermark is None:
        return image
    position = site.watermark_position or "bottom_right"
    if position not in WATERMARK_POSITIONS:
        position = "bottom_right"
    return _paste_watermark(
        image,
        watermark,
        position=position,
        opacity=float(site.watermark_opacity or 0.35),
    )


def _is_near_white(pixel, threshold: int = 240) -> bool:
    r, g, b = pixel[:3]
    return r >= threshold and g >= threshold and b >= threshold


def _outer_white_mask(rgb: Image.Image, threshold: int = 240) -> Image.Image:
    """Opaque where connected near-white runs in from the edges (JPEG padding)."""
    source = rgb.convert("RGB")
    width, height = source.size
    pixels = source.load()
    seen = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def try_push(x: int, y: int) -> None:
        if x < 0 or y < 0 or x >= width or y >= height:
            return
        index = y * width + x
        if seen[index]:
            return
        if not _is_near_white(pixels[x, y], threshold):
            return
        seen[index] = 1
        queue.append((x, y))

    for x in range(width):
        try_push(x, 0)
        try_push(x, height - 1)
    for y in range(height):
        try_push(0, y)
        try_push(width - 1, y)

    while queue:
        x, y = queue.popleft()
        try_push(x - 1, y)
        try_push(x + 1, y)
        try_push(x, y - 1)
        try_push(x, y + 1)

    mask = Image.new("L", (width, height), 0)
    out = mask.load()
    for y in range(height):
        row = y * width
        for x in range(width):
            if seen[row + x]:
                out[x, y] = 255
    return mask.filter(ImageFilter.MaxFilter(3))


def _remove_outer_white(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    background = _outer_white_mask(rgba)
    alpha = ImageChops.multiply(rgba.split()[3], ImageOps.invert(background))
    rgba.putalpha(alpha)
    return rgba


def _crop_to_visible(image: Image.Image, pad: int = 2) -> Image.Image:
    bbox = image.getbbox()
    if not bbox:
        return image
    left, top, right, bottom = bbox
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(image.width, right + pad)
    bottom = min(image.height, bottom + pad)
    return image.crop((left, top, right, bottom))


def _prepare_logo(image: Image.Image) -> Image.Image:
    """Keep PNG alpha, or punch JPEG/white padding to transparent WebP."""
    rgba = image.convert("RGBA")
    extrema = rgba.getextrema()
    alpha_min = extrema[3][0] if len(extrema) > 3 else 255
    if alpha_min >= 255:
        rgba = _remove_outer_white(rgba)
    return _crop_to_visible(rgba)


def to_webp_upload(uploaded, *, kind: str | None = None) -> InMemoryUploadedFile:
    if hasattr(uploaded, "seek"):
        uploaded.seek(0)
    try:
        image = Image.open(uploaded)
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("فایل تصویر معتبر نیست.") from exc

    normalized_kind = normalize_media_kind(kind)
    image = ImageOps.exif_transpose(image)

    max_side = _max_side_for_kind(normalized_kind)
    if max(image.size) > max_side:
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    has_alpha = image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    )
    keep_alpha = False
    if normalized_kind == "logo":
        image = _prepare_logo(image)
        keep_alpha = True
    else:
        image = image.convert("RGBA" if has_alpha else "RGB")

    site = _site_settings()
    image = _apply_watermark(image, site, normalized_kind)

    if image.mode == "RGBA" and not keep_alpha:
        flat_bg = Image.new("RGB", image.size, (255, 255, 255))
        flat_bg.paste(image, mask=image.split()[3])
        image = flat_bg
    elif image.mode != "RGBA":
        image = image.convert("RGB")

    buffer = BytesIO()
    save_kwargs: dict = {"format": "WEBP", "method": 6}
    if keep_alpha:
        save_kwargs["lossless"] = True
        save_kwargs["exact"] = True
    else:
        save_kwargs["quality"] = WEBP_QUALITY
    image.save(buffer, **save_kwargs)
    buffer.seek(0)

    stem = Path(getattr(uploaded, "name", "") or "image").stem or "image"
    return InMemoryUploadedFile(
        file=buffer,
        field_name=getattr(uploaded, "field_name", "file"),
        name=f"{stem}.webp",
        content_type="image/webp",
        size=buffer.getbuffer().nbytes,
        charset=None,
    )


def absolute_media_url(path: str | None, request=None) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    public_base = getattr(settings, "MEDIA_PUBLIC_BASE_URL", "").rstrip("/")
    if public_base:
        return f"{public_base}{path}"
    if request is not None:
        return request.build_absolute_uri(path)
    return path


def asset_absolute_url(asset, request=None) -> str:
    if not asset:
        return ""
    file_field = getattr(asset, "file", None)
    if file_field and getattr(file_field, "name", None):
        return absolute_media_url(file_field.url, request)
    src = getattr(asset, "src", "") or ""
    return absolute_media_url(src, request) if src else ""
