from django.db import models


class SiteVisitDaily(models.Model):
    day = models.DateField(unique=True)
    pageviews = models.PositiveIntegerField(default=0)
    uniques = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-day"]
        verbose_name = "بازدید روزانه"
        verbose_name_plural = "بازدیدهای روزانه"

    def __str__(self) -> str:
        return f"{self.day}: {self.pageviews} pv / {self.uniques} uv"


class SiteVisitVisitor(models.Model):
    day = models.DateField()
    visitor_key = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["day", "visitor_key"],
                name="uniq_visit_day_visitor",
            )
        ]
        indexes = [models.Index(fields=["day"])]
        verbose_name = "بازدیدکننده روزانه"
        verbose_name_plural = "بازدیدکنندگان روزانه"

    def __str__(self) -> str:
        return f"{self.day} · {self.visitor_key[:8]}"


class SiteVisitHit(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    visitor_key = models.CharField(max_length=64, blank=True)
    path = models.CharField(max_length=200, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    browser = models.CharField(max_length=32, blank=True, db_index=True)
    device = models.CharField(max_length=16, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "browser"]),
            models.Index(fields=["-created_at", "device"]),
        ]
        verbose_name = "بازدید صفحه"
        verbose_name_plural = "بازدیدهای صفحه"

    def __str__(self) -> str:
        return f"{self.created_at} · {self.path or '/'}"
