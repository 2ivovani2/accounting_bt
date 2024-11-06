from django.contrib import admin
from partners_bot.models import *

@admin.register(Processor)
class ProcessorAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "is_ready_to_get_money", "username", "verified_usr", "is_superuser", "balance", "comission")
    search_fields = ("id", "username", "telegram_chat_id", "balance")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["username", "telegram_chat_id", "verified_usr", "is_ready_to_get_money", "is_superuser", "balance", "comission", "insurance_deposit"]
        }),
    )