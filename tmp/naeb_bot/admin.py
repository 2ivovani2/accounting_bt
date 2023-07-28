from django.contrib import admin
from naeb_bot.models import *

@admin.register(NaebBotUser)
class NaebBotUserAdmin(admin.ModelAdmin):
    """
        Описание пользователей naeb bot в админской панели
    """
    list_display = ("id", "username", "verified_usr")
    search_fields = ("id", "username")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["username", "telegram_chat_id", "verified_usr"]

        }),
    )
