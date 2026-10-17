from django.contrib.auth import get_user_model
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsStaffUser
from apps.accounts.models import StaffProfile
from apps.accounts.staff_permissions import (
    STAFF_PERMISSION_KEYS,
    STAFF_PERMISSION_LABELS,
    normalize_permissions,
    permissions_for_django_user,
)
from apps.foundation.models import OpsSettings, SiteSettings
from apps.foundation.serializers import OpsSettingsSerializer, SiteSettingsSerializer

User = get_user_model()

RESERVED_USERNAMES = {
    "admin",
    "administrator",
    "root",
    "superuser",
    "superadmin",
    "test",
    "demo",
    "user",
    "staff",
}


def validate_staff_username(username: str) -> str | None:
    value = username.strip()
    if not value:
        return "نام کاربری الزامی است."
    if value.lower() in RESERVED_USERNAMES:
        return "این نام کاربری رزرو شده است."
    if len(value) < 3:
        return "نام کاربری باید حداقل ۳ کاراکتر باشد."
    return None


def validate_staff_password(password: str, *, require_complexity: bool) -> str | None:
    if not password:
        return "رمز عبور الزامی است."
    if not require_complexity:
        if len(password) < 8:
            return "رمز عبور باید حداقل ۸ کاراکتر باشد."
        return None
    if len(password) < 10:
        return "رمز پیچیده باید حداقل ۱۰ کاراکتر باشد."
    if not any(c.isalpha() for c in password):
        return "رمز پیچیده باید شامل حروف انگلیسی باشد."
    if not any(c.isdigit() for c in password):
        return "رمز پیچیده باید شامل عدد باشد."
    if password.lower() == password or password.upper() == password:
        return "رمز پیچیده باید ترکیبی از حروف بزرگ و کوچک باشد."
    return None


def get_or_create_site_settings() -> SiteSettings:
    page, _ = SiteSettings.objects.get_or_create(
        key="default",
        defaults={
            "name_fa": "بنیاد دکتر مجتهدی",
            "name_en": "Dr. Mojtahedi Foundation",
        },
    )
    return page


class PublicSiteSettingsView(APIView):
    """Public subset used by the foundation site (banner, brand, logos)."""

    permission_classes = [AllowAny]

    def get(self, request):
        data = SiteSettingsSerializer(
            get_or_create_site_settings(), context={"request": request}
        ).data
        return Response(
            {
                "nameFa": data.get("nameFa"),
                "nameEn": data.get("nameEn"),
                "tagline": data.get("tagline"),
                "taglineFa": data.get("taglineFa"),
                "brandColors": data.get("brandColors"),
                "siteBanner": data.get("siteBanner"),
                "logo": data.get("logo"),
                "logoDark": data.get("logoDark"),
                "favicon": data.get("favicon"),
                "url": data.get("url"),
                "email": data.get("email"),
                "phone": data.get("phone"),
                "phoneSecondary": data.get("phoneSecondary"),
                "whatsapp": data.get("whatsapp"),
                "whatsappHref": data.get("whatsappHref"),
                "address": data.get("address"),
                "social": data.get("social"),
                "contactDescription": data.get("contactDescription"),
                "contactHours": data.get("contactHours"),
                "homeSections": data.get("homeSections"),
                "homeSectionOrder": data.get("homeSectionOrder"),
                "heroTemplate": data.get("heroTemplate"),
                "heroAutoplayDelay": data.get("heroAutoplayDelay"),
            }
        )


class AdminSiteSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def _page(self):
        return get_or_create_site_settings()

    def get(self, request):
        return Response(
            SiteSettingsSerializer(self._page(), context={"request": request}).data
        )

    def patch(self, request):
        serializer = SiteSettingsSerializer(
            self._page(),
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminOpsSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def _page(self):
        page, _ = OpsSettings.objects.get_or_create(key="default")
        return page

    def get(self, request):
        return Response(OpsSettingsSerializer(self._page()).data)

    def patch(self, request):
        serializer = OpsSettingsSerializer(
            self._page(),
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class AdminStaffViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated, IsStaffUser]
    pagination_class = None
    queryset = User.objects.filter(is_staff=True).select_related("staff_profile").order_by(
        "username"
    )

    def _can_manage_staff(self, request) -> bool:
        actor = request.user
        if not actor or not actor.is_authenticated:
            return False
        if actor.is_superuser:
            return True
        return "settings" in permissions_for_django_user(actor)

    def _row(self, user: User) -> dict:
        display_name = f"{user.first_name} {user.last_name}".strip()
        return {
            "id": user.pk,
            "username": user.username,
            "firstName": user.first_name or "",
            "lastName": user.last_name or "",
            "displayName": display_name or user.username,
            "email": user.email,
            "isActive": user.is_active,
            "isSuperuser": user.is_superuser,
            "permissions": permissions_for_django_user(user),
            "lastLogin": user.last_login.isoformat() if user.last_login else None,
            "lastLoginIp": getattr(getattr(user, "staff_profile", None), "last_login_ip", "")
            or "",
            "dateJoined": user.date_joined.isoformat() if user.date_joined else None,
        }

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not self._can_manage_staff(request):
            self.permission_denied(
                request,
                message="دسترسی مدیریت کاربران پنل را ندارید.",
            )

    def list(self, request, *args, **kwargs):
        return Response([self._row(user) for user in self.get_queryset()])

    def create(self, request, *args, **kwargs):
        actor = request.user
        username = str(request.data.get("username") or "").strip()
        password = str(request.data.get("password") or "")
        email = str(request.data.get("email") or "").strip()
        first_name = str(request.data.get("firstName") or "").strip()
        last_name = str(request.data.get("lastName") or "").strip()
        is_superuser = bool(request.data.get("isSuperuser"))
        permissions = normalize_permissions(request.data.get("permissions"))
        require_complexity = bool(request.data.get("requirePasswordComplexity", True))

        if not username or not password:
            return Response(
                {"detail": "نام کاربری و رمز عبور الزامی است."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        username_error = validate_staff_username(username)
        if username_error:
            return Response({"detail": username_error}, status=status.HTTP_400_BAD_REQUEST)
        if is_superuser and not actor.is_superuser:
            return Response(
                {"detail": "فقط ابرکاربر می‌تواند ابرکاربر بسازد."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if User.objects.filter(username=username).exists():
            return Response(
                {"detail": "این نام کاربری قبلاً ثبت شده است."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not is_superuser and not permissions:
            return Response(
                {"detail": "حداقل یک بخش دسترسی را انتخاب کنید."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        password_error = validate_staff_password(
            password, require_complexity=require_complexity
        )
        if password_error:
            return Response({"detail": password_error}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=is_superuser,
            first_name=first_name,
            last_name=last_name,
        )
        StaffProfile.objects.update_or_create(
            user=user,
            defaults={"permissions": [] if is_superuser else permissions},
        )
        return Response(self._row(user), status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        actor = request.user
        user = self.get_object()
        if "email" in request.data:
            user.email = str(request.data.get("email") or "").strip()
        if "firstName" in request.data:
            user.first_name = str(request.data.get("firstName") or "").strip()
        if "lastName" in request.data:
            user.last_name = str(request.data.get("lastName") or "").strip()
        if "isActive" in request.data:
            next_active = bool(request.data.get("isActive"))
            if not next_active and actor.username == user.username:
                return Response(
                    {"detail": "نمی‌توانید حساب خودتان را غیرفعال کنید."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not next_active and user.is_superuser:
                others = User.objects.filter(
                    is_staff=True, is_superuser=True, is_active=True
                ).exclude(pk=user.pk)
                if not others.exists():
                    return Response(
                        {"detail": "حداقل یک ادمین فعال باید بماند."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            user.is_active = next_active
        if "isSuperuser" in request.data:
            next_super = bool(request.data.get("isSuperuser"))
            if next_super != user.is_superuser and not actor.is_superuser:
                return Response(
                    {"detail": "فقط ابرکاربر می‌تواند سطح ابرکاربر را تغییر دهد."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            user.is_superuser = next_super
        password = str(request.data.get("password") or "")
        if password:
            require_complexity = bool(request.data.get("requirePasswordComplexity", True))
            password_error = validate_staff_password(
                password, require_complexity=require_complexity
            )
            if password_error:
                return Response(
                    {"detail": password_error}, status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(password)
        user.save()

        if "permissions" in request.data:
            if user.is_superuser:
                StaffProfile.objects.update_or_create(
                    user=user, defaults={"permissions": []}
                )
            else:
                permissions = normalize_permissions(request.data.get("permissions"))
                if not permissions:
                    return Response(
                        {"detail": "حداقل یک بخش دسترسی را انتخاب کنید."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                StaffProfile.objects.update_or_create(
                    user=user, defaults={"permissions": permissions}
                )

        user = User.objects.select_related("staff_profile").get(pk=user.pk)
        return Response(self._row(user))

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        if request.user.username == user.username:
            return Response(
                {"detail": "نمی‌توانید حساب خودتان را غیرفعال کنید."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_superuser:
            others = User.objects.filter(
                is_staff=True, is_superuser=True, is_active=True
            ).exclude(pk=user.pk)
            if not others.exists():
                return Response(
                    {"detail": "حداقل یک ادمین فعال باید بماند."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminStaffPermissionMetaView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        return Response(
            {
                "keys": list(STAFF_PERMISSION_KEYS),
                "labels": STAFF_PERMISSION_LABELS,
            }
        )
