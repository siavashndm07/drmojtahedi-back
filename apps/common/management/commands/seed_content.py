from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.ai.models import AiChatConfig
from apps.archive.models import ArchiveItem, OralHistoryInterview
from apps.content.models import (
    Article,
    ArticleCategory,
    LibraryItem,
    NewsCategory,
    NewsItem,
)
from apps.foundation.models import CollaborateOption, FoundationProject, OrganMember, Sponsor
from apps.heritage.models import Person, Place, TimelineEvent


class Command(BaseCommand):
    help = "Seed foundation content and create default admin user"

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@drmojtahedi.local", "admin123456")
            self.stdout.write(self.style.SUCCESS("Created admin / admin123456"))
        else:
            self.stdout.write("Admin user already exists")

        people = [
            {
                "slug": "samuel-jordan",
                "title": "ساموئل جوردن",
                "name": "ساموئل جوردن",
                "role": "بنیان‌گذار دبیرستان البرز",
                "kind": "colleague",
                "description": "مبلّغ و آموزگار آمریکایی که دبیرستان البرز را پایه‌گذاری کرد.",
            },
            {
                "slug": "hossein-mahjoobi",
                "title": "حسین محجوبی",
                "name": "استاد حسین محجوبی اصیل",
                "role": "نقاش · عضو هیئت موسس",
                "kind": "founder",
                "description": "فارغ‌التحصیل البرز؛ اهداکنندهٔ آثار برای یادمان/موزه.",
            },
            {
                "slug": "alireza-shoja-pour",
                "title": "علیرضا شجاع‌پور",
                "name": "استاد علیرضا شجاع‌پور",
                "role": "شاعر · دانش‌آموختهٔ البرز",
                "kind": "student",
                "description": "شاعر و فارغ‌التحصیل دبیرستان ماندگار البرز.",
            },
        ]
        for row in people:
            Person.objects.update_or_create(slug=row["slug"], defaults=row)

        places = [
            {
                "slug": "lahijan",
                "title": "لاهیجان",
                "description": "زادگاه دکتر محمدعلی مجتهدی گیلانی.",
                "location": "گیلان، ایران",
                "lat": 37.207,
                "lng": 50.0039,
                "historical_significance": "محل تولد و سال‌های کودکی مجتهدی.",
            },
            {
                "slug": "alborz-high-school",
                "title": "دبیرستان البرز",
                "description": "حدود ۳۴ سال تحت ریاست دکتر مجتهدی.",
                "location": "تهران",
                "lat": 35.736,
                "lng": 51.41,
                "historical_significance": "نام مجتهدی با البرز گره خورده است.",
            },
            {
                "slug": "sharif-university",
                "title": "دانشگاه صنعتی شریف",
                "description": "بنیان‌گذاری‌شده به همت دکتر مجتهدی.",
                "location": "تهران",
                "lat": 35.7036,
                "lng": 51.3515,
                "historical_significance": "مجتهدی نخستین نایب‌التولیه بود.",
            },
        ]
        for row in places:
            Place.objects.update_or_create(slug=row["slug"], defaults=row)

        categories = [
            {"slug": "ehda", "title": "اهداء", "sort_order": 1},
            {"slug": "entesharat", "title": "انتشارات", "sort_order": 2},
            {"slug": "khabar", "title": "خبر", "sort_order": 3},
            {"slug": "etelaieh", "title": "اطلاعیه", "sort_order": 4},
        ]
        for row in categories:
            NewsCategory.objects.update_or_create(slug=row["slug"], defaults=row)

        news = [
            {
                "slug": "ehdaye-asar-mahjoobi",
                "title": "اهدای آثار استاد محجوبی",
                "description": "اهدا برای اهداف آموزشی و یادمان/موزه.",
                "category": "اهداء",
                "body": "آثار استاد حسین محجوبی به بنیاد اهدا شد.",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "آثار استاد حسین محجوبی به بنیاد اهدا شد.",
                    },
                    {
                        "type": "tip",
                        "text": "این آثار برای یادمان و موزه نگهداری می‌شوند.",
                    },
                ],
                "date_label": "۱۴۰۳/۰۵/۰۲",
            },
            {
                "slug": "chap-sheshom-be-mamlekatoon",
                "title": "چاپ ششم به مملکتتون خدمت کنید",
                "description": "اعلام انتشار چاپ ششم.",
                "category": "انتشارات",
                "body": "کتاب ارزشمند در آستانهٔ انتشار مجدد است.",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "کتاب ارزشمند در آستانهٔ انتشار مجدد است.",
                    },
                    {
                        "type": "h2",
                        "text": "چاپ ششم",
                    },
                    {
                        "type": "paragraph",
                        "text": "علاقه‌مندان می‌توانند از بخش انتشارات پیگیری کنند.",
                    },
                ],
                "date_label": "۱۴۰۳",
            },
        ]
        for row in news:
            NewsItem.objects.update_or_create(slug=row["slug"], defaults=row)

        for row in [
            {"slug": "miras", "title": "میراث", "sort_order": 1},
            {"slug": "tarikh", "title": "تاریخ", "sort_order": 2},
        ]:
            ArticleCategory.objects.update_or_create(slug=row["slug"], defaults=row)

        articles = [
            {
                "slug": "moalem-alborz",
                "title": "معلم البرز",
                "description": "روایت مدیریت آموزشی دکتر مجتهدی در البرز.",
                "category": "میراث",
                "subtitle": "از نظم کلاس تا خدمت به کشور",
                "tags": ["البرز", "آموزش", "میراث"],
                "date_label": "۱۴۰۳",
                "reading_time_minutes": 8,
            },
            {
                "slug": "bonyangozari-sharif",
                "title": "بنیان‌گذاری شریف",
                "description": "نقطهٔ عطف تأسیس دانشگاه صنعتی.",
                "category": "تاریخ",
                "tags": ["شریف", "دانشگاه"],
                "date_label": "۱۴۰۳",
                "reading_time_minutes": 6,
            },
        ]
        for row in articles:
            Article.objects.update_or_create(slug=row["slug"], defaults=row)

        books = [
            {
                "slug": "be-mamlekatoon-khedmat-konid",
                "title": "به مملکتتون خدمت کنید",
                "description": "برگرفته از خاطرات و گفتارهای دکتر مجتهدی.",
                "author": "دکتر محمدعلی مجتهدی گیلانی",
                "year": "چاپ ششم · ۱۴۰۳",
                "item_type": "book",
            },
            {
                "slug": "khaterat-dr-mojtahedi",
                "title": "خاطرات دکتر محمدعلی مجتهدی",
                "description": "متن تاریخ شفاهی به کوشش حبیب لاجوردی.",
                "author": "حبیب لاجوردی",
                "year": "۱۳۸۰",
                "item_type": "book",
            },
        ]
        for row in books:
            LibraryItem.objects.update_or_create(slug=row["slug"], defaults=row)

        archive = [
            {
                "slug": "tablo-harekat-va-zendegi",
                "title": "تابلوی «حرکت و زندگی»",
                "type": "object",
                "description": "اثر استاد حسین محجوبی؛ اهداشده برای یادمان.",
                "collection": "آثار اهدایی",
                "date_label": "۱۴۰۳/۰۵/۰۲",
                "creator": "استاد حسین محجوبی",
            },
            {
                "slug": "oral-history-interview",
                "title": "مصاحبهٔ تاریخ شفاهی",
                "type": "audio",
                "description": "مصاحبه با دکتر مجتهدی در ۱۹۸۸.",
                "collection": "تاریخ شفاهی",
                "date_label": "۱۹۸۸",
            },
        ]
        for row in archive:
            ArchiveItem.objects.update_or_create(slug=row["slug"], defaults=row)

        OralHistoryInterview.objects.update_or_create(
            slug="oral-history-interview",
            defaults={
                "title": "مصاحبهٔ تاریخ شفاهی با دکتر مجتهدی",
                "subtitle": "بنیاد مطالعات ایران · ۱۹۸۸",
                "year": "۱۹۸۸",
                "duration_label": "حدود ۴۵ دقیقه",
                "narrator": "دکتر محمدعلی مجتهدی گیلانی",
                "collection": "تاریخ شفاهی ایران",
                "description": "روایت تحصیل، البرز و شریف.",
                "transcript_excerpt": "به مملکت‌تان خدمت کنید…",
                "related_href": "/archive/oral-history-interview",
                "related_label": "آیتم آرشیو",
            },
        )

        sponsors = [
            {
                "slug": "bina-pardazesh-gil",
                "title": "بینا پردازش گیل",
                "kind": "organization",
                "logo_label": "بینا",
                "description": "حامی سازمانی بنیاد.",
            },
            {
                "slug": "kambiz-ghaderi",
                "title": "آقای دکتر کامبیز قادری",
                "kind": "individual",
                "logo_label": "ک.ق",
                "description": "حامی گرامی بنیاد.",
            },
        ]
        for row in sponsors:
            Sponsor.objects.update_or_create(slug=row["slug"], defaults=row)

        FoundationProject.objects.update_or_create(
            slug="khane-farhangi-va-yadman",
            defaults={
                "title": "خانه فرهنگی و بنای یادمان",
                "description": "پروژهٔ یادمان و خانهٔ فرهنگی.",
                "phase": "مطالعات",
                "location": "لاهیجان",
            },
        )

        OrganMember.objects.get_or_create(
            name="بهزاد اشتری",
            defaults={"role": "عضو هیئت موسس", "group": "boards", "note": "فارغ‌التحصیل البرز"},
        )

        TimelineEvent.objects.get_or_create(
            year="۱۲۸۷",
            title="تولد در لاهیجان",
            defaults={
                "description": "محمدعلی مجتهدی گیلانی در لاهیجان زاده شد.",
                "location": "لاهیجان",
                "category": "آغاز",
                "related_item_ids": ["place-lahijan"],
            },
        )

        collaborate = [
            {
                "slug": "davtalabi",
                "title": "همکاری داوطلبانه",
                "description": "همراهی در آرشیو، گالری، پروژه‌ها و برنامه‌های فرهنگی بنیاد.",
                "kind": "volunteer",
            },
            {
                "slug": "sherakat-sazmani",
                "title": "شراکت سازمانی",
                "description": "همکاری دانشگاه‌ها، انجمن‌ها و مؤسسات فرهنگی با بنیاد.",
                "kind": "partner",
            },
            {
                "slug": "hamkari-pazhoheshi",
                "title": "همکاری پژوهشی",
                "description": "پروژه‌های مشترک دربارهٔ تاریخ آموزش، البرز و شریف.",
                "kind": "research",
            },
            {
                "slug": "ehdaye-asar",
                "title": "اهدای سند و اثر",
                "description": "سپردن عکس، سند، کتاب یا اثر هنری.",
                "kind": "donate-artifact",
            },
            {
                "slug": "hamyari-sherkati",
                "title": "حمایت شرکتی",
                "description": "اسپانسرشیپ برنامه‌ها و پروژه‌های عام‌المنفعهٔ بنیاد.",
                "kind": "corporate",
            },
        ]
        for row in collaborate:
            CollaborateOption.objects.update_or_create(slug=row["slug"], defaults=row)

        AiChatConfig.objects.update_or_create(
            key="default",
            defaults={
                "enabled": True,
                "welcome_message": "سلام! من دستیار بنیاد فرهنگی دکتر مجتهدی هستم.",
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed completed"))
