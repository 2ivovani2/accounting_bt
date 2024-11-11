from django.contrib import admin
from partners_bot.models import *

@admin.register(Processor)
class ProcessorAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "is_ready_to_get_money", "username", "verified_usr", "is_superuser", "balance", "comission", "insurance_deposit", )
    search_fields = ("id", "username", "telegram_chat_id", "balance")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["username", "telegram_chat_id", "verified_usr", "is_ready_to_get_money", "is_superuser", "balance", "comission", "insurance_deposit", "info", "has_active_paying_insurance_apply", "amount_to_accept"]
        }),
    )

@admin.register(InsurancePayment)
class InsurancePaymentAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "owner", "payment_sum_rub", "payment_sum_usdt", "is_applied")
    search_fields = ("id", "owner__username", "payment_sum_rub", "payment_sum_usdt",)

    fieldsets = (

        ("Основные параметры", {
            "fields": ["owner", "payment_sum_rub", "payment_sum_usdt", "is_applied"]
        }),
    )

@admin.register(Reks)
class ReksAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "reks_owner", "who_use_reks", "card_number", "card_owner_name" ,"bank_name", "is_archived")
    search_fields = ("id", "reks_owner__username", "bank_name", "card_number", "card_owner_name")

    fieldsets = (
        ("Основные параметры", {
            "fields": ["reks_owner", "who_use_reks", "bank_name", "card_number", "card_owner_name", "sbp_phone_number", "is_archived"]
        }),
    )