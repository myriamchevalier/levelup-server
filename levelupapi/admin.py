from django.contrib import admin
from levelupapi.models import Gamer, GameType, Game, Event, EventGamer
# Register your models here.
admin.site.register(Gamer)
admin.site.register(Game)
admin.site.register(GameType)
admin.site.register(Event)
admin.site.register(EventGamer)
