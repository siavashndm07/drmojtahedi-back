from django.urls import path
from apps.ai.views import AiChatConfigView, AiChatView
urlpatterns = [
    path("ai/chat/config/", AiChatConfigView.as_view()),
    path("ai/chat/", AiChatView.as_view()),
]
