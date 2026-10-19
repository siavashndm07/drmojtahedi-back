from django.db import models

from apps.common.models import SluggedContentModel, TimeStampedModel


class FoundationProject(SluggedContentModel):
    phase = models.CharField(max_length=80, blank=True)
    location = models.CharField(max_length=255, blank=True)
    href = models.CharField(max_length=255, blank=True)


class Sponsor(SluggedContentModel):
    kind = models.CharField(max_length=40, default="individual")
    logo_label = models.CharField(max_length=40, blank=True)
    cover_image = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sponsor_covers",
    )
    logo_image = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sponsor_logos",
    )


class OrganMember(TimeStampedModel):
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    group = models.CharField(max_length=40, default="boards")
    location = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="published")


class UsefulLink(TimeStampedModel):
    """Public «پیوندهای مفید» managed from admin."""

    title = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    logo = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="useful_link_logos",
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "پیوند مفید"
        verbose_name_plural = "پیوندهای مفید"

    def __str__(self):
        return self.title


class CharterChapter(TimeStampedModel):
    key = models.SlugField(unique=True)
    title = models.CharField(max_length=255)
    body = models.TextField()


class SiteSettings(TimeStampedModel):
    """Singleton foundation site settings (Bina SiteSettings subset)."""

    key = models.SlugField(unique=True, default="default")
    name_fa = models.CharField(max_length=120, blank=True, default="بنیاد دکتر مجتهدی")
    name_en = models.CharField(max_length=120, blank=True, default="Dr. Mojtahedi Foundation")
    tagline = models.CharField(max_length=255, blank=True)
    tagline_fa = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    company = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    phone_href = models.CharField(max_length=64, blank=True)
    phone_secondary = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    whatsapp_href = models.CharField(max_length=128, blank=True)
    address = models.TextField(blank=True)
    url = models.URLField(blank=True)
    contact_description = models.TextField(blank=True)
    contact_hours = models.CharField(max_length=200, blank=True)
    map_lat = models.FloatField(null=True, blank=True)
    map_lon = models.FloatField(null=True, blank=True)
    social = models.JSONField(default=dict, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.JSONField(default=list, blank=True)
    brand_colors = models.JSONField(default=dict, blank=True)
    site_banner = models.JSONField(default=dict, blank=True)
    logo_asset = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_logos",
    )
    logo_dark_asset = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_logos_dark",
    )
    favicon_asset = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_favicons",
    )
    watermark_enabled = models.BooleanField(default=False)
    watermark_asset = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="site_watermarks",
    )
    watermark_opacity = models.FloatField(default=0.35)
    watermark_position = models.CharField(
        max_length=16,
        choices=(
            ("bottom_right", "پایین راست"),
            ("bottom_left", "پایین چپ"),
            ("top_right", "بالا راست"),
            ("top_left", "بالا چپ"),
            ("center", "وسط"),
        ),
        default="bottom_right",
    )
    watermark_apply_kinds = models.JSONField(default=list, blank=True)
    home_sections = models.JSONField(default=dict, blank=True)
    home_section_order = models.JSONField(default=list, blank=True)
    footer_nav = models.JSONField(default=list, blank=True)
    hero_template = models.CharField(max_length=32, blank=True, default="fullBleed")
    hero_autoplay_delay = models.PositiveIntegerField(default=5600)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.name_fa or self.key


class OpsSettings(TimeStampedModel):
    """Payment / ops settings for donations (Bina OpsSettings subset)."""

    class Gateway(models.TextChoices):
        NONE = "none", "بدون درگاه"
        ZARINPAL = "zarinpal", "زرین‌پال"
        ZIBAL = "zibal", "زیبال"
        SEP = "sep", "سامان (SEP)"
        PASARGAD = "pasargad", "پاسارگاد (PEP)"
        MELLAT = "mellat", "بانک ملت (به‌پرداخت)"
        IRANKISH = "irankish", "تجارت / ایران‌کیش"

    key = models.SlugField(unique=True, default="default")
    cash_on_delivery = models.BooleanField(default=False)
    card_to_card = models.BooleanField(default=True)
    card_holder = models.CharField(max_length=120, blank=True)
    card_number = models.CharField(max_length=32, blank=True)
    donate_message = models.TextField(
        blank=True,
        default="حمایت شما صرف برنامه‌های فرهنگی و عام‌المنفعهٔ بنیاد می‌شود.",
    )
    gateway = models.CharField(
        max_length=16,
        choices=Gateway.choices,
        default=Gateway.NONE,
    )
    payment_gateways = models.JSONField(default=dict, blank=True)
    sandbox = models.BooleanField(default=True)
    merchant_id = models.CharField(max_length=128, blank=True)
    gateway_merchant_code = models.CharField(max_length=64, blank=True)
    gateway_private_key = models.TextField(blank=True)

    class AiProvider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        GROK = "grok", "Grok (xAI)"

    ai_enabled = models.BooleanField(default=False)
    ai_provider = models.CharField(
        max_length=16,
        choices=AiProvider.choices,
        default=AiProvider.OPENAI,
    )
    ai_api_key = models.CharField(max_length=256, blank=True)
    ai_model = models.CharField(max_length=128, blank=True)
    ai_base_url = models.CharField(max_length=300, blank=True)
    ai_welcome_message = models.CharField(
        max_length=400,
        blank=True,
        default="سلام! درباره بنیاد، پروژه‌ها، کمک‌ها و میراث دکتر مجتهدی بپرسید.",
    )
    ai_system_extra = models.TextField(blank=True)

    class Meta:
        verbose_name = "تنظیمات عملیاتی"
        verbose_name_plural = "تنظیمات عملیاتی"

    def __str__(self):
        return f"ops:{self.key}"


class HeroSlide(TimeStampedModel):
    slug = models.SlugField(max_length=120, unique=True, allow_unicode=True)
    image = models.CharField(max_length=500, blank=True)
    image_asset = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hero_slides",
    )
    mobile_image = models.CharField(max_length=500, blank=True)
    mobile_image_asset = models.ForeignKey(
        "archive_app.MediaAsset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hero_slides_mobile",
    )
    eyebrow = models.CharField(max_length=120, blank=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    cta_label = models.CharField(max_length=120, blank=True)
    cta_href = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    weekdays = models.JSONField(
        default=list,
        blank=True,
        help_text="روزهای نمایش بر اساس ISO (۱=دوشنبه … ۷=یکشنبه). خالی یعنی همه روزها.",
    )

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "اسلاید هیرو"
        verbose_name_plural = "اسلایدهای هیرو"

    def __str__(self) -> str:
        return self.title

    def is_visible_on(self, iso_weekday: int) -> bool:
        days = self.weekdays or []
        if not days:
            return True
        return iso_weekday in days


class CollaborateOption(SluggedContentModel):
    kind = models.CharField(max_length=40, default="volunteer")
