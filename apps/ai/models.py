from django.db import models
from apps.common.models import TimeStampedModel
class AiChatConfig(TimeStampedModel):
    key = models.SlugField(unique=True, default="default")
    enabled = models.BooleanField(default=True)
    welcome_message = models.TextField(default="سلام! من دستیار بنیاد هستم.")
