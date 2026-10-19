from datetime import datetime
from pathlib import Path
from urllib.request import urlretrieve

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

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


def _cover(filename: str, url: str) -> str:
    dest = Path(settings.MEDIA_ROOT) / "news" / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_size < 1000:
        urlretrieve(url, dest)
    return f"/media/news/{filename}"


def _published(value: str):
    parsed = datetime.strptime(value, "%Y-%m-%d %H:%M")
    return timezone.make_aware(parsed, timezone.get_current_timezone())


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
                "title": "اهدای ۲ اثر از آثار و تابلوهای ارزشمند استاد محجوبی به بنیاد",
                "description": "استاد حسین محجوبی دو اثر «حرکت و زندگی» و «برج البرز» را برای اهداف آموزشی و موزه به بنیاد اهدا کرد.",
                "category": "اهداء",
                "author": "هیئت رئیسه بنیاد",
                "status": "published",
                "source": "https://drmojtahedi.com/NewsDetails.aspx?News_ID=50905b3f-dbfc-4032-bd5d-d1527f6f4ba3",
                "cover": _cover(
                    "mahjoobi.jpg",
                    "https://drmojtahedi.com/Images/Img_News/14030502202638.jpg",
                ),
                "cover_tone": "pine",
                "date_label": "۲ مرداد ۱۴۰۳",
                "published_at": _published("2024-07-23 20:26"),
                "body": "مطابق توافقنامه، دو اثر «حرکت و زندگی» و «برج البرز» به بنیاد اهدا شد.",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "مطابق توافقنامه و صورتجلسهٔ اعضای هیئت مدیره با استاد حسین محجوبی اصیل، دو اثر «حرکت و زندگی» و «برج البرز» برای توسعهٔ اهداف آموزشی و فرهنگی عام‌المنفعه — از جمله پیگیری مقدمات ساخت یادمان و موزه در لاهیجان یا تهران — و نگهداری دائمی اثر دوم در موزه، به بنیاد اهدا شده است.",
                    },
                    {
                        "type": "paragraph",
                        "text": "این توافقنامه با حضور و امضای ابراهیم ثابت، بازرس قانونی بنیاد، و محمدحسن/سعید محجوبی، فرزند ارشد و نمایندهٔ تام‌الاختیار استاد، مبادله شد. اثر «حرکت و زندگی» و معادل وجه فروش آن، کمک بلاعوض استاد به بنیاد است و در گزارش فصلی به ناظر مالیاتی ارائه می‌شود.",
                    },
                    {
                        "type": "h2",
                        "text": "جزئیات آثار",
                    },
                    {
                        "type": "ul",
                        "text": "«حرکت و زندگی»: ۱۰۰×۱۰۰ سانتی‌متر، رنگ‌وروغن روی بوم\n«برج البرز»: ۸۰×۱۲۰ سانتی‌متر، رنگ‌وروغن روی بوم؛ ایده‌ای برای بنای یادمان در تپه‌های اطراف لاهیجان",
                    },
                ],
            },
            {
                "slug": "chap-sheshom-be-mamlekatoon",
                "title": "چاپ ششم کتاب «به مملکتتون خدمت کنید» در آستانهٔ انتشار",
                "description": "زندگی‌نامهٔ دست‌نویس دکتر مجتهدی برای ششمین بار، در ۱۵۰۰ نسخه، به چاپ می‌رسد.",
                "category": "انتشارات",
                "author": "هیئت رئیسه بنیاد",
                "status": "published",
                "source": "https://drmojtahedi.com/NewsDetails.aspx?News_ID=6f69ed90-2167-4564-a65e-94e24a74f671",
                "cover": _cover(
                    "book-sixth.jpg",
                    "https://drmojtahedi.com/uploads/mamlakat%201.jpg",
                ),
                "cover_tone": "bronze",
                "date_label": "۴ اردیبهشت ۱۴۰۳",
                "published_at": _published("2024-04-23 16:31"),
                "body": "کتاب «به مملکتتون خدمت کنید» برای ششمین بار در مرحلهٔ چاپ است.",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "کتاب «به مملکتتون خدمت کنید»، حاوی زندگی‌نامهٔ دست‌نویس زنده‌یاد دکتر محمدعلی مجتهدی گیلانی، برای ششمین بار در مرحلهٔ چاپ و انتشار قرار گرفته است.",
                    },
                    {
                        "type": "paragraph",
                        "text": "تهیه‌کننده و مدیر پروژه مهندس نادر قادسی است و نشر لاک، وابسته به انتشارات امین‌الضرب، آن را منتشر می‌کند. گردآورنده سورنا امیری است. چاپ ششم ۱۵۰۰ نسخه است و در بهار ۱۴۰۳ در اختیار علاقه‌مندان قرار می‌گیرد. پنج چاپ پیشین روی هم ۵۹۰۰ نسخه بوده است.",
                    },
                    {
                        "type": "h2",
                        "text": "خرید",
                    },
                    {
                        "type": "ul",
                        "text": "فروش اینترنتی: chare.ir\nفروشگاه اختران، میدان انقلاب، بازارچهٔ کتاب\nپخش کتاب گزیده: ۰۲۱۶۶۴۹۲۹۶۲\nفروش تعداد: ۰۹۱۲۲۴۵۱۳۷۴، سورنا امیری",
                    },
                    {
                        "type": "paragraph",
                        "text": "اسناد، تصاویر و دست‌نوشته‌های کتاب از سایت alborz-drmojtahedi.com هم در دسترس است.",
                    },
                ],
            },
            {
                "slug": "moafiat-maliati-1401",
                "title": "ابلاغ معافیت ۱۰۰٪ مالیاتی عملکرد سال ۱۴۰۱ بنیاد",
                "description": "پس از رسیدگی در دارایی شرق تهران، معافیت کامل مالیاتی عملکرد ۱۴۰۱ رسماً ابلاغ شد.",
                "category": "اطلاعیه",
                "author": "هیئت رئیسه بنیاد",
                "status": "published",
                "source": "https://drmojtahedi.com/NewsDetails.aspx?News_ID=4b288d74-a5a8-4776-bc5e-b106c2a2a4ce",
                "cover": _cover(
                    "tax-1401.jpg",
                    "https://drmojtahedi.com/uploads/Moafeyt%201401.jpg",
                ),
                "cover_tone": "ink",
                "date_label": "۲۴ بهمن ۱۴۰۲",
                "published_at": _published("2024-02-13 16:51"),
                "body": "بنیاد از معافیت کامل مالیاتی عملکرد سال ۱۴۰۱ برخوردار شد.",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "با ابلاغ تشخیص، بنیاد فرهنگی دکتر مجتهدی از معافیت کامل مالیاتی عملکرد سال ۱۴۰۱ برخوردار شده است.",
                    },
                    {
                        "type": "paragraph",
                        "text": "معافیت مؤسسات عام‌المنفعه پس از ارائهٔ دفاتر قانونی، اسناد، اظهارنامه و رسیدگی ممیز، تأیید رئیس گروه مالیاتی و تصدیق ناظر مالیاتی اعمال می‌شود. این فرآیند برای بنیاد در دارایی شرق تهران طی و رسماً ابلاغ شد.",
                    },
                ],
            },
            {
                "slug": "dastur-abdolmaleki-chabahar",
                "title": "دستور پیگیری توافقنامهٔ بنیاد با منطقهٔ آزاد چابهار",
                "description": "دبیر شورای عالی مناطق آزاد خواستار گزارش فوری از اجرای توافقنامه با بنیاد شد.",
                "category": "خبر",
                "author": "هیئت رئیسه بنیاد",
                "status": "published",
                "source": "https://drmojtahedi.com/NewsDetails.aspx?News_ID=137b3df8-3283-4117-899c-a9b24650616d",
                "cover": _cover(
                    "chabahar.jpg",
                    "https://drmojtahedi.com/uploads/Dastor%20e%20AbdilM.jpg",
                ),
                "cover_tone": "bronze",
                "date_label": "۲۴ مهر ۱۴۰۲",
                "published_at": _published("2023-10-16 13:50"),
                "body": "دکتر عبدالملکی دستور تهیهٔ گزارش فوری از توافقنامه با سازمان منطقهٔ آزاد چابهار را صادر کرد.",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "مهدی‌پور، عضو هیئت مدیره و خزانه‌دار و نمایندهٔ تام‌الاختیار بنیاد، با دکتر حجت‌الله عبدالملکی، دبیر شورای عالی مناطق آزاد، دیدار کرد. پس از این دیدار، به دکتر مقدم، مدیرعامل سازمان منطقهٔ آزاد چابهار، دستور تهیهٔ گزارش فوری از توافقنامه داده شد.",
                    },
                    {
                        "type": "paragraph",
                        "text": "توافق‌نامهٔ سال ۱۳۹۹ و اصلاحیهٔ ۱۴۰۰ برای خدمت به روستاهای کم‌برخوردار چابهار، دشتیاری و کنارک مبادله شده بود. بنیاد می‌گوید بخش عمدهٔ تعهدات مالی منطقه، از جمله سهم‌الشرکهٔ مراکز هماهنگی کارآفرینی و ادامهٔ ساخت پنج مدرسه، اجرا نشده است.",
                    },
                    {
                        "type": "paragraph",
                        "text": "هیئت رئیسه امیدوار است با این دستور، تعهدات منطقه پس از توافق تکمیلی ادامه پیدا کند. نمایندگی بنیاد در چابهار آمادگی استقرار و ازسرگیری فعالیت‌های متوقف‌شده را اعلام کرده است.",
                    },
                ],
            },
        ]
        for row in news:
            NewsItem.objects.update_or_create(
                slug=row["slug"],
                defaults={**row, "cover_image": None},
            )

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
