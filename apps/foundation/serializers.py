import re

from rest_framework import serializers

from apps.archive.media_utils import asset_absolute_url
from apps.archive.models import MediaAsset
from apps.foundation.models import (
    CollaborateOption,
    FoundationProject,
    HeroSlide,
    OpsSettings,
    OrganMember,
    SiteSettings,
    Sponsor,
    UsefulLink,
)

HERO_TEMPLATE_IDS = {"fullBleed", "splitText", "minimalCta"}
HERO_AUTOPLAY_MIN_MS = 2000
HERO_AUTOPLAY_MAX_MS = 30000
HERO_AUTOPLAY_DEFAULT_MS = 5600
from apps.foundation.simple_html import sanitize_simple_html

BRAND_COLOR_DEFAULTS = {
    "pine": "#2F7F78",
    "pineDark": "#246661",
    "mint": "#D8EDEB",
    "mintSoft": "#F0F7F6",
    "mintDeep": "#2F7F78",
}

BRAND_COLOR_KEYS = tuple(BRAND_COLOR_DEFAULTS.keys())
_HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{6})$")

HOME_SECTION_DEFAULTS = {
    "hero": True,
    "donate": True,
    "timeline": True,
    "news": True,
    "projects": True,
    "archive": True,
    "magazine": True,
    "sponsors": True,
    "partners": True,
    "supportCta": True,
}
HOME_SECTION_ORDER_KEYS = tuple(HOME_SECTION_DEFAULTS.keys())


def merge_home_sections(raw) -> dict:
    merged = dict(HOME_SECTION_DEFAULTS)
    if not isinstance(raw, dict):
        return merged
    for key, default in HOME_SECTION_DEFAULTS.items():
        if key in raw:
            merged[key] = bool(raw[key])
        else:
            merged[key] = default
    return merged


def normalize_home_section_order(raw) -> list:
    fallback = list(HOME_SECTION_ORDER_KEYS)
    if not isinstance(raw, list) or not raw:
        return fallback
    valid = set(HOME_SECTION_ORDER_KEYS)
    seen = set()
    order = []
    for item in raw:
        key = str(item or "").strip()
        if key not in valid or key in seen:
            continue
        seen.add(key)
        order.append(key)
    for key in HOME_SECTION_ORDER_KEYS:
        if key in seen:
            continue
        default_index = fallback.index(key)
        insert_at = len(order)
        for index, existing in enumerate(order):
            if fallback.index(existing) > default_index:
                insert_at = index
                break
        order.insert(insert_at, key)
        seen.add(key)
    return order

BODY_BACKGROUND_DEFAULTS = {
    "mode": "solid",
    "color": "#F9F6F3",
    "colorEnd": "#F0F7F6",
    "angle": 165,
}


def _normalize_hex_color(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    if not trimmed.startswith("#"):
        trimmed = f"#{trimmed}"
    if not _HEX_COLOR_RE.fullmatch(trimmed):
        return None
    return trimmed.upper()


def merge_body_background(raw) -> dict:
    merged = dict(BODY_BACKGROUND_DEFAULTS)
    if not isinstance(raw, dict):
        return merged
    mode = str(raw.get("mode") or "").strip().lower()
    if mode in ("solid", "gradient"):
        merged["mode"] = mode
    color = _normalize_hex_color(raw.get("color", ""))
    if color:
        merged["color"] = color
    color_end = _normalize_hex_color(raw.get("colorEnd", ""))
    if color_end:
        merged["colorEnd"] = color_end
    try:
        angle = int(raw.get("angle"))
        merged["angle"] = angle % 360
    except (TypeError, ValueError):
        pass
    return merged


def merge_brand_colors(raw) -> dict:
    merged = dict(BRAND_COLOR_DEFAULTS)
    if isinstance(raw, dict):
        for key in BRAND_COLOR_KEYS:
            normalized = _normalize_hex_color(raw.get(key, ""))
            if normalized:
                merged[key] = normalized
        accent = _normalize_hex_color(raw.get("accent", ""))
        if accent:
            merged["accent"] = accent
        if "bodyBackground" in raw:
            merged["bodyBackground"] = merge_body_background(raw.get("bodyBackground"))
        else:
            merged["bodyBackground"] = dict(BODY_BACKGROUND_DEFAULTS)
    else:
        merged["bodyBackground"] = dict(BODY_BACKGROUND_DEFAULTS)
    return merged


SITE_BANNER_DEFAULTS = {
    "enabled": False,
    "mode": "text",
    "message": "",
    "imageUrl": "",
    "imageId": "",
    "link": "",
    "linkLabel": "اطلاعات بیشتر",
}

DEFAULT_WATERMARK_KINDS = ("news", "articles", "people", "archive", "hero", "sponsors")


def merge_site_banner(raw) -> dict:
    merged = dict(SITE_BANNER_DEFAULTS)
    if not isinstance(raw, dict):
        return merged
    merged["enabled"] = bool(raw.get("enabled"))
    mode = str(raw.get("mode") or "text").strip().lower()
    merged["mode"] = "image" if mode == "image" else "text"
    merged["message"] = str(raw.get("message") or "")
    merged["imageUrl"] = str(raw.get("imageUrl") or "")
    merged["imageId"] = str(raw.get("imageId") or "")
    merged["link"] = str(raw.get("link") or "")
    merged["linkLabel"] = str(raw.get("linkLabel") or SITE_BANNER_DEFAULTS["linkLabel"])
    return merged


def _normalize_watermark_kinds(value) -> list[str]:
    allowed = set(DEFAULT_WATERMARK_KINDS)
    if not isinstance(value, (list, tuple)):
        return list(DEFAULT_WATERMARK_KINDS)
    cleaned = [str(item).strip() for item in value if str(item).strip() in allowed]
    return cleaned or list(DEFAULT_WATERMARK_KINDS)



class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoundationProject
        fields = "__all__"


class SponsorSerializer(serializers.ModelSerializer):
    logoLabel = serializers.CharField(source="logo_label", required=False, allow_blank=True)
    coverImageId = serializers.UUIDField(
        source="cover_image_id", required=False, allow_null=True
    )
    logoImageId = serializers.UUIDField(
        source="logo_image_id", required=False, allow_null=True
    )
    coverImage = serializers.SerializerMethodField()
    logoImage = serializers.SerializerMethodField()

    class Meta:
        model = Sponsor
        fields = (
            "id",
            "slug",
            "title",
            "description",
            "status",
            "source",
            "kind",
            "logo_label",
            "logoLabel",
            "coverImageId",
            "logoImageId",
            "coverImage",
            "logoImage",
            "created_at",
            "updated_at",
        )

    def _asset_payload(self, asset):
        if not asset:
            return None
        url = asset_absolute_url(asset, self.context.get("request"))
        if not url:
            return None
        return {
            "id": str(asset.id),
            "src": url,
            "alt": asset.display_alt or "",
        }

    def get_coverImage(self, obj: Sponsor):
        return self._asset_payload(obj.cover_image)

    def get_logoImage(self, obj: Sponsor):
        return self._asset_payload(obj.logo_image)

    def validate_cover_image_id(self, value):
        if value is None:
            return None
        _resolve_asset(value)
        return value

    def validate_logo_image_id(self, value):
        if value is None:
            return None
        _resolve_asset(value)
        return value


class OrganMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganMember
        fields = "__all__"


class CollaborateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaborateOption
        fields = "__all__"


def _normalize_hero_template(raw) -> str:
    value = str(raw or "").strip()
    if value in HERO_TEMPLATE_IDS:
        return value
    return "fullBleed"


def _normalize_hero_autoplay(raw) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return HERO_AUTOPLAY_DEFAULT_MS
    return max(HERO_AUTOPLAY_MIN_MS, min(HERO_AUTOPLAY_MAX_MS, value))


def _resolve_asset(value):
    if value is None:
        return None
    asset = MediaAsset.objects.filter(pk=value).first()
    if not asset:
        raise serializers.ValidationError("فایل رسانه یافت نشد.")
    return asset


class UsefulLinkSerializer(serializers.ModelSerializer):
    sortOrder = serializers.IntegerField(source="sort_order", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    logoId = serializers.UUIDField(source="logo_id", required=False, allow_null=True)
    logoImage = serializers.SerializerMethodField()

    class Meta:
        model = UsefulLink
        fields = (
            "id",
            "title",
            "url",
            "sort_order",
            "sortOrder",
            "is_active",
            "isActive",
            "logoId",
            "logoImage",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def get_logoImage(self, obj: UsefulLink):
        asset = obj.logo
        if not asset:
            return None
        url = asset_absolute_url(asset, self.context.get("request"))
        if not url:
            return None
        return {
            "id": str(asset.id),
            "src": url,
            "alt": asset.display_alt or obj.title,
        }

    def validate_logo_id(self, value):
        if value is None:
            return None
        _resolve_asset(value)
        return value


class SiteSettingsSerializer(serializers.ModelSerializer):
    nameFa = serializers.CharField(source="name_fa", required=False, allow_blank=True)
    nameEn = serializers.CharField(source="name_en", required=False, allow_blank=True)
    taglineFa = serializers.CharField(source="tagline_fa", required=False, allow_blank=True)
    phoneHref = serializers.CharField(source="phone_href", required=False, allow_blank=True)
    phoneSecondary = serializers.CharField(
        source="phone_secondary", required=False, allow_blank=True
    )
    whatsappHref = serializers.CharField(
        source="whatsapp_href", required=False, allow_blank=True
    )
    contactDescription = serializers.CharField(
        source="contact_description", required=False, allow_blank=True
    )
    contactHours = serializers.CharField(
        source="contact_hours", required=False, allow_blank=True
    )
    mapLat = serializers.FloatField(source="map_lat", required=False, allow_null=True)
    mapLon = serializers.FloatField(source="map_lon", required=False, allow_null=True)
    metaDescription = serializers.CharField(
        source="meta_description", required=False, allow_blank=True
    )
    metaKeywords = serializers.JSONField(source="meta_keywords", required=False)
    social = serializers.JSONField(required=False)
    logo = serializers.SerializerMethodField()
    logoId = serializers.UUIDField(
        source="logo_asset_id", required=False, allow_null=True
    )
    logoDark = serializers.SerializerMethodField()
    logoDarkId = serializers.UUIDField(
        source="logo_dark_asset_id", required=False, allow_null=True
    )
    favicon = serializers.SerializerMethodField()
    faviconId = serializers.UUIDField(
        source="favicon_asset_id", required=False, allow_null=True
    )
    brandColors = serializers.JSONField(source="brand_colors", required=False)
    siteBanner = serializers.JSONField(source="site_banner", required=False)
    watermarkEnabled = serializers.BooleanField(
        source="watermark_enabled", required=False
    )
    watermarkOpacity = serializers.FloatField(
        source="watermark_opacity", required=False, min_value=0.05, max_value=1
    )
    watermarkPosition = serializers.CharField(
        source="watermark_position", required=False, allow_blank=True
    )
    watermarkApplyKinds = serializers.JSONField(
        source="watermark_apply_kinds", required=False
    )
    watermark = serializers.SerializerMethodField()
    watermarkId = serializers.UUIDField(
        source="watermark_asset_id", required=False, allow_null=True
    )
    homeSections = serializers.JSONField(source="home_sections", required=False)
    homeSectionOrder = serializers.JSONField(
        source="home_section_order", required=False
    )
    heroTemplate = serializers.CharField(
        source="hero_template", required=False, allow_blank=True
    )
    heroAutoplayDelay = serializers.IntegerField(
        source="hero_autoplay_delay", required=False
    )
    footerNav = serializers.JSONField(source="footer_nav", required=False)

    class Meta:
        model = SiteSettings
        fields = (
            "id",
            "key",
            "nameFa",
            "nameEn",
            "tagline",
            "taglineFa",
            "summary",
            "company",
            "email",
            "phone",
            "phoneHref",
            "phoneSecondary",
            "whatsapp",
            "whatsappHref",
            "address",
            "url",
            "contactDescription",
            "contactHours",
            "mapLat",
            "mapLon",
            "social",
            "metaDescription",
            "metaKeywords",
            "brandColors",
            "siteBanner",
            "logo",
            "logoId",
            "logoDark",
            "logoDarkId",
            "favicon",
            "faviconId",
            "watermarkEnabled",
            "watermarkOpacity",
            "watermarkPosition",
            "watermarkApplyKinds",
            "watermark",
            "watermarkId",
            "homeSections",
            "homeSectionOrder",
            "heroTemplate",
            "heroAutoplayDelay",
            "footerNav",
            "created_at",
            "updated_at",
        )

    def get_logo(self, obj):
        return asset_absolute_url(obj.logo_asset, self.context.get("request"))

    def get_logoDark(self, obj):
        return asset_absolute_url(obj.logo_dark_asset, self.context.get("request"))

    def get_favicon(self, obj):
        return asset_absolute_url(obj.favicon_asset, self.context.get("request"))

    def get_watermark(self, obj):
        return asset_absolute_url(obj.watermark_asset, self.context.get("request"))

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["brandColors"] = merge_brand_colors(instance.brand_colors)
        data["siteBanner"] = merge_site_banner(instance.site_banner)
        data["watermarkApplyKinds"] = _normalize_watermark_kinds(
            instance.watermark_apply_kinds
        )
        data["homeSections"] = merge_home_sections(instance.home_sections)
        data["homeSectionOrder"] = normalize_home_section_order(
            instance.home_section_order
        )
        data["heroTemplate"] = _normalize_hero_template(instance.hero_template)
        data["heroAutoplayDelay"] = _normalize_hero_autoplay(instance.hero_autoplay_delay)
        # Keep image URL in banner for clients that only store imageId.
        banner = data["siteBanner"]
        if banner.get("imageId") and not banner.get("imageUrl"):
            asset = MediaAsset.objects.filter(pk=banner["imageId"]).first()
            if asset:
                banner["imageUrl"] = asset_absolute_url(
                    asset, self.context.get("request")
                )
                data["siteBanner"] = banner
        return data

    def validate_homeSections(self, value):
        if value is None:
            return dict(HOME_SECTION_DEFAULTS)
        if not isinstance(value, dict):
            raise serializers.ValidationError("فرمت بخش‌های صفحه اصلی نامعتبر است.")
        return merge_home_sections(value)

    def validate_heroTemplate(self, value):
        return _normalize_hero_template(value)

    def validate_heroAutoplayDelay(self, value):
        return _normalize_hero_autoplay(value)

    def validate_footerNav(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("فرمت پیوندهای فوتر نامعتبر است.")
        cleaned = []
        allowed_icons = {
            "home",
            "person",
            "biography",
            "timeline",
            "foundation",
            "charter",
            "organs",
            "students",
            "news",
            "magazine",
            "books",
            "projects",
            "gallery",
            "photos",
            "video",
            "collaborate",
            "memories",
            "support",
            "sponsors",
            "contact",
            "search",
            "places",
            "archive",
            "sparkles",
        }
        for index, section in enumerate(value[:8]):
            if not isinstance(section, dict):
                continue
            links = []
            for link in (section.get("links") or [])[:16]:
                if not isinstance(link, dict):
                    continue
                label = str(link.get("label") or "").strip()[:80]
                href = str(link.get("href") or "").strip()[:300]
                if not label and not href:
                    continue
                icon = link.get("icon")
                links.append(
                    {
                        "label": label,
                        "href": href,
                        "icon": icon if icon in allowed_icons else "sparkles",
                        "enabled": bool(link.get("enabled", True)),
                    }
                )
            title = str(section.get("title") or "").strip()[:80]
            if not title and not links:
                continue
            icon = section.get("icon")
            section_id = str(section.get("id") or "").strip()[:40] or f"section-{index + 1}"
            cleaned.append(
                {
                    "id": section_id,
                    "title": title or "پیوندها",
                    "icon": icon if icon in allowed_icons else "sparkles",
                    "enabled": bool(section.get("enabled", True)),
                    "links": links,
                }
            )
        return cleaned

    def validate_homeSectionOrder(self, value):
        if value is None:
            return list(HOME_SECTION_ORDER_KEYS)
        if not isinstance(value, list):
            raise serializers.ValidationError("فرمت ترتیب بخش‌ها نامعتبر است.")
        return normalize_home_section_order(value)

    def validate_brandColors(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError("فرمت رنگ‌های برند نامعتبر است.")
        allowed = set(BRAND_COLOR_KEYS) | {"accent"}
        cleaned = {}
        for key in value:
            if key == "bodyBackground":
                continue
            if key not in allowed:
                continue
            normalized = _normalize_hex_color(value.get(key, ""))
            if not normalized:
                raise serializers.ValidationError(f"رنگ {key} نامعتبر است.")
            cleaned[key] = normalized
        if "bodyBackground" in value:
            cleaned["bodyBackground"] = merge_body_background(
                value.get("bodyBackground")
            )
        return cleaned

    def validate_siteBanner(self, value):
        if value is None:
            return dict(SITE_BANNER_DEFAULTS)
        if not isinstance(value, dict):
            raise serializers.ValidationError("فرمت بنر اعلان نامعتبر است.")
        cleaned = merge_site_banner(value)
        image_id = cleaned.get("imageId") or ""
        if image_id:
            _resolve_asset(image_id)
        return cleaned

    def validate_watermarkApplyKinds(self, value):
        return _normalize_watermark_kinds(value)

    def validate_watermarkPosition(self, value):
        allowed = {
            "bottom_right",
            "bottom_left",
            "top_right",
            "top_left",
            "center",
        }
        normalized = str(value or "bottom_right").strip()
        if normalized not in allowed:
            raise serializers.ValidationError("موقعیت واترمارک نامعتبر است.")
        return normalized

    def validate_logo_asset_id(self, value):
        if value is None:
            return None
        _resolve_asset(value)
        return value

    def validate_logo_dark_asset_id(self, value):
        if value is None:
            return None
        _resolve_asset(value)
        return value

    def validate_favicon_asset_id(self, value):
        if value is None:
            return None
        _resolve_asset(value)
        return value

    def validate_watermark_asset_id(self, value):
        if value is None:
            return None
        _resolve_asset(value)
        return value

    def update(self, instance, validated_data):
        brand_colors = validated_data.pop("brand_colors", None)
        if brand_colors is not None:
            merged = merge_brand_colors(instance.brand_colors)
            merged.update(brand_colors)
            validated_data["brand_colors"] = merged

        site_banner = validated_data.pop("site_banner", None)
        if site_banner is not None:
            validated_data["site_banner"] = merge_site_banner(site_banner)

        return super().update(instance, validated_data)




class OpsSettingsSerializer(serializers.ModelSerializer):
    SUPPORTED_GATEWAYS = {
        OpsSettings.Gateway.NONE,
        OpsSettings.Gateway.ZARINPAL,
        OpsSettings.Gateway.ZIBAL,
        OpsSettings.Gateway.SEP,
        OpsSettings.Gateway.PASARGAD,
        OpsSettings.Gateway.MELLAT,
        OpsSettings.Gateway.IRANKISH,
    }

    cashOnDelivery = serializers.BooleanField(source="cash_on_delivery", required=False)
    cardToCard = serializers.BooleanField(source="card_to_card", required=False)
    cardHolder = serializers.CharField(source="card_holder", required=False, allow_blank=True)
    cardNumber = serializers.CharField(source="card_number", required=False, allow_blank=True)
    donateMessage = serializers.CharField(
        source="donate_message", required=False, allow_blank=True
    )
    defaultGateway = serializers.CharField(source="gateway", required=False)
    paymentGateways = serializers.SerializerMethodField()
    merchantId = serializers.CharField(source="merchant_id", required=False, allow_blank=True)
    gatewayMerchantCode = serializers.CharField(
        source="gateway_merchant_code", required=False, allow_blank=True
    )
    gatewayPrivateKey = serializers.CharField(
        source="gateway_private_key",
        required=False,
        allow_blank=True,
        write_only=True,
    )
    merchantIdSet = serializers.SerializerMethodField()
    gatewayPrivateKeySet = serializers.SerializerMethodField()
    gatewayLabel = serializers.SerializerMethodField()
    aiEnabled = serializers.BooleanField(source="ai_enabled", required=False)
    aiProvider = serializers.ChoiceField(
        source="ai_provider",
        choices=OpsSettings.AiProvider.choices,
        required=False,
    )
    aiApiKey = serializers.CharField(
        source="ai_api_key",
        required=False,
        allow_blank=True,
        write_only=True,
    )
    aiApiKeySet = serializers.SerializerMethodField()
    aiModel = serializers.CharField(source="ai_model", required=False, allow_blank=True)
    aiBaseUrl = serializers.CharField(
        source="ai_base_url", required=False, allow_blank=True
    )
    aiWelcomeMessage = serializers.CharField(
        source="ai_welcome_message", required=False, allow_blank=True
    )
    aiSystemExtra = serializers.CharField(
        source="ai_system_extra", required=False, allow_blank=True
    )

    class Meta:
        model = OpsSettings
        fields = (
            "id",
            "key",
            "cashOnDelivery",
            "cardToCard",
            "cardHolder",
            "cardNumber",
            "donateMessage",
            "gateway",
            "defaultGateway",
            "gatewayLabel",
            "paymentGateways",
            "sandbox",
            "merchantId",
            "merchantIdSet",
            "gatewayMerchantCode",
            "gatewayPrivateKey",
            "gatewayPrivateKeySet",
            "aiEnabled",
            "aiProvider",
            "aiApiKey",
            "aiApiKeySet",
            "aiModel",
            "aiBaseUrl",
            "aiWelcomeMessage",
            "aiSystemExtra",
            "created_at",
            "updated_at",
        )

    def get_merchantIdSet(self, obj):
        return bool(obj.merchant_id)

    def get_gatewayPrivateKeySet(self, obj):
        return bool(obj.gateway_private_key)

    def get_aiApiKeySet(self, obj):
        return bool(obj.ai_api_key)

    def get_gatewayLabel(self, obj):
        return obj.get_gateway_display()

    def get_paymentGateways(self, obj: OpsSettings) -> list:
        from apps.foundation.gateway_services import serialize_payment_gateways_admin

        return serialize_payment_gateways_admin(obj)

    def validate_gateway(self, value: str) -> str:
        if value not in self.SUPPORTED_GATEWAYS:
            raise serializers.ValidationError("درگاه پشتیبانی نمی‌شود.")
        return value

    def validate_donateMessage(self, value):
        return sanitize_simple_html(value)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("merchantId", None)
        if "donateMessage" in data:
            data["donateMessage"] = sanitize_simple_html(data.get("donateMessage") or "")
        return data

    def update(self, instance, validated_data):
        payment_gateways_in = self.initial_data.get("paymentGateways")
        if payment_gateways_in is not None:
            from apps.foundation.gateway_services import merge_payment_gateways_from_admin

            validated_data["payment_gateways"] = merge_payment_gateways_from_admin(
                instance,
                payment_gateways_in if isinstance(payment_gateways_in, list) else None,
            )

        private_key = validated_data.get("gateway_private_key")
        if private_key is None or str(private_key).strip() == "":
            validated_data.pop("gateway_private_key", None)

        ai_api_key = validated_data.get("ai_api_key")
        if ai_api_key is None or str(ai_api_key).strip() == "":
            validated_data.pop("ai_api_key", None)

        merchant_id = validated_data.get("merchant_id")
        if merchant_id is not None and str(merchant_id).strip() == "":
            validated_data.pop("merchant_id", None)

        instance = super().update(instance, validated_data)

        if payment_gateways_in is not None or "gateway" in validated_data:
            from apps.foundation.gateway_services import sync_legacy_flat_fields

            sync_legacy_flat_fields(instance)
            instance.save(
                update_fields=[
                    "gateway",
                    "sandbox",
                    "merchant_id",
                    "gateway_merchant_code",
                    "gateway_private_key",
                    "payment_gateways",
                ]
            )

        return instance


class HeroSlideSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="slug", read_only=True)
    image = serializers.SerializerMethodField()
    mobileImage = serializers.SerializerMethodField()
    ctaLabel = serializers.CharField(source="cta_label")
    ctaHref = serializers.CharField(source="cta_href")

    class Meta:
        model = HeroSlide
        fields = (
            "id",
            "slug",
            "image",
            "mobileImage",
            "eyebrow",
            "title",
            "subtitle",
            "description",
            "ctaLabel",
            "ctaHref",
        )

    def get_image(self, obj: HeroSlide) -> str:
        return asset_absolute_url(obj.image_asset, self.context.get("request")) or obj.image or ""

    def get_mobileImage(self, obj: HeroSlide) -> str:
        return (
            asset_absolute_url(obj.mobile_image_asset, self.context.get("request"))
            or obj.mobile_image
            or ""
        )


class AdminHeroSlideSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="slug", read_only=True)
    image = serializers.SerializerMethodField()
    imageId = serializers.UUIDField(source="image_asset_id", required=False, allow_null=True)
    mobileImage = serializers.SerializerMethodField()
    mobileImageId = serializers.UUIDField(
        source="mobile_image_asset_id", required=False, allow_null=True
    )
    ctaLabel = serializers.CharField(source="cta_label", required=False, allow_blank=True)
    ctaHref = serializers.CharField(source="cta_href", required=False, allow_blank=True)
    sortOrder = serializers.IntegerField(source="sort_order", required=False)
    isActive = serializers.BooleanField(source="is_active", required=False)
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = HeroSlide
        fields = (
            "id",
            "slug",
            "image",
            "imageId",
            "mobileImage",
            "mobileImageId",
            "eyebrow",
            "title",
            "subtitle",
            "description",
            "ctaLabel",
            "ctaHref",
            "sortOrder",
            "isActive",
            "weekdays",
        )

    def get_image(self, obj: HeroSlide) -> str:
        return asset_absolute_url(obj.image_asset, self.context.get("request")) or obj.image or ""

    def get_mobileImage(self, obj: HeroSlide) -> str:
        return (
            asset_absolute_url(obj.mobile_image_asset, self.context.get("request"))
            or obj.mobile_image
            or ""
        )

    def validate_weekdays(self, value):
        days = sorted({int(day) for day in (value or [])})
        if any(day < 1 or day > 7 for day in days):
            raise serializers.ValidationError("روز هفته نامعتبر است.")
        if len(days) >= 7:
            return []
        return days

    def validate_image_asset_id(self, value):
        _resolve_asset(value)
        return value

    def validate_mobile_image_asset_id(self, value):
        _resolve_asset(value)
        return value

    def create(self, validated_data):
        slide = super().create(validated_data)
        self._sync_urls(slide)
        return slide

    def update(self, instance, validated_data):
        slide = super().update(instance, validated_data)
        self._sync_urls(slide)
        return slide

    def _sync_urls(self, slide: HeroSlide) -> None:
        request = self.context.get("request")
        slide.image = asset_absolute_url(slide.image_asset, request) or slide.image
        slide.mobile_image = asset_absolute_url(slide.mobile_image_asset, request) or ""
        slide.save(update_fields=["image", "mobile_image"])
