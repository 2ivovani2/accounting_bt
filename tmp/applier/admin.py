from django.contrib import admin
from applier.models import *

@admin.register(ApplyUser)
class UserAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "username", "verified_usr", "is_superuser")
    search_fields = ("id", "username", "telegram_chat_id")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["username", "telegram_chat_id", "verified_usr", "is_superuser"]
        }),
    )

    