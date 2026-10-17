from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
from apps.accounts.jwt_utils import decode_token
from apps.accounts.models import MemberProfile

User = get_user_model()


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header.startswith("Bearer "):
            return None
        token = header[7:].strip()
        if not token:
            return None
        try:
            payload = decode_token(token)
        except Exception as exc:
            raise exceptions.AuthenticationFailed("توکن نامعتبر است") from exc

        kind = payload.get("kind")
        sub = payload.get("sub")
        if kind == "staff":
            try:
                user = User.objects.get(username=sub)
            except User.DoesNotExist as exc:
                raise exceptions.AuthenticationFailed("کاربر یافت نشد") from exc
            if not user.is_staff:
                raise exceptions.AuthenticationFailed("دسترسی کارکنان لازم است")
            request.auth_kind = "staff"
            return (user, payload)
        if kind == "member":
            try:
                profile = MemberProfile.objects.get(phone=sub)
            except MemberProfile.DoesNotExist as exc:
                raise exceptions.AuthenticationFailed("عضو یافت نشد") from exc
            request.auth_kind = "member"
            request.member_profile = profile
            user = profile.user or User(username=f"member:{sub}")
            return (user, payload)
        raise exceptions.AuthenticationFailed("نوع توکن نامعتبر است")
