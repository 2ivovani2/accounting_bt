from django.contrib import admin
from applier.models import *

@admin.register(ApplyUser)
class UserAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "username", "verified_usr", "is_superuser", "balance")
    search_fields = ("id", "username", "telegram_chat_id", "balance")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["username", "telegram_chat_id", "verified_usr", "is_superuser", "balance"]
        }),
    )

@admin.register(Withdraw)
class WithdrawAdmin(admin.ModelAdmin):
    """
        Описание выводов в админской панели
    """
    
    list_display = ("withdraw_id", "withdraw_sum", "withdraw_owner", "withdraw_date", "is_applied", "withdraw_address", "course", "usdt_sum")
    search_fields = ("cheque_id", "cheque_sum", "cheque_owner", "withdraw_address", "course", "usdt_sum")

    fieldsets = (
        ("Основные параметры", {
            "fields": ["withdraw_id", "withdraw_sum", "withdraw_owner", "withdraw_date", "is_applied", "withdraw_address", "course", "usdt_sum"]
        }),
    )


@admin.register(Cheque)
class ChequeAdmin(admin.ModelAdmin):
    """
        Описание чеков в админской панели
    """
    list_display = ("cheque_id", "cheque_sum", "cheque_owner", "cheque_date", "is_applied", "is_denied")
    search_fields = ("cheque_id", "cheque_sum", "cheque_owner")

    fieldsets = (
        ("Основные параметры", {
            "fields": ["cheque_id", "cheque_sum", "cheque_owner", "cheque_date", "is_aplied", "is_denied"]
        }),
    )
