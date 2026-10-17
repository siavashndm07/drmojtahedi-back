from django.contrib import admin
from apps.heritage.models import Person, Place, Institution, TimelineEvent
admin.site.register(Person)
admin.site.register(Place)
admin.site.register(Institution)
admin.site.register(TimelineEvent)
