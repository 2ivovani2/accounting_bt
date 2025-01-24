from django.contrib import admin
from partners_bot.models import *

@admin.register(Processor)
class ProcessorAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "username", "is_ready_to_get_money", "verified_usr", "is_superuser", "balance", "comission", "insurance_deposit", "device_token")
    search_fields = ("id", "username", "telegram_chat_id", "balance")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["telegram_chat_id", "username", "verified_usr", "is_ready_to_get_money", "is_ready_to_get_money_first", "is_superuser", "balance", "comission", "insurance_deposit", "info", "has_active_paying_insurance_apply", "amount_to_accept"]
        }),
        ("Токен для девайса процессора", {
            "fields": ["device_token"]
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

@admin.register(AutoAcceptCheque)
class AutoAcceptChequeAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "hash", "amount", "description" , "reks", "created_at", "is_applied", "is_denied")
    search_fields = ("id", "hash")

    fieldsets = (
        ("Основные параметры", {
            "fields":["hash", "amount", "description" , "is_applied", "reks", "redirect_url", "success_webhook", "is_denied"]
        }),
    )

@admin.register(Reks)
class ReksAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "reks_owner", "card_number", "card_owner_name" ,"bank_name", "is_archived")
    search_fields = ("id", "reks_owner__username", "bank_name", "card_number", "card_owner_name")

    fieldsets = (
        ("Основные параметры", {
            "fields": ["reks_owner", "bank_name", "card_number", "card_owner_name", "sbp_phone_number", "is_archived"]
        }),
    )