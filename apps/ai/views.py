from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.ai.models import AiChatConfig

DEFAULT_WELCOME = "سلام! من دستیار بنیاد فرهنگی دکتر مجتهدی هستم."

class AiChatConfigView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        cfg = AiChatConfig.objects.filter(key="default").first()
        return Response({
            "enabled": cfg.enabled if cfg else True,
            "welcomeMessage": cfg.welcome_message if cfg else DEFAULT_WELCOME,
        })

class AiChatView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        messages = request.data.get("messages") or []
        last = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last = str(m.get("content") or "")
                break
        q = last.lower()
        if any(k in q for k in ("عضویت","عضو")):
            reply = "برای عضویت از صفحهٔ عضویت و ورود پیامکی استفاده کنید."
        elif any(k in q for k in ("کمک","اهدا","حمایت")):
            reply = "کمک بلاعوض از مسیر حمایت و فرم اهدا در دسترس است."
        elif any(k in q for k in ("خبر","اخبار")):
            reply = "تازه‌ها در بخش اخبار بنیاد منتشر می‌شود."
        else:
            reply = "می‌توانید دربارهٔ عضویت، حمایت، اخبار، آرشیو یا زندگی‌نامه بپرسید."
        return Response({"reply": reply, "provider": "rules"})
