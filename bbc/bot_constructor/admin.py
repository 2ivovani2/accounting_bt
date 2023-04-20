from django.contrib import admin
from bot_constructor.models import *

@admin.register(TGPayment)
class TGPaymentAdmin(admin.ModelAdmin):
    list_display = ("payment_id", "amt", "fact_amt", "owner", "status")
    search_fields = ("payment_id", "amt", "fact_amt", "owner", "status")

    fieldsets = (
        ("Money info", {
            "fields": ("payment_id", "amt", "owner")
        }),

    )

@admin.register(AdminTransaction)
class AdminTransactionAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about users of web interface 
    """
    list_display = ("payment_id", "status", "payment_sum", "comission", "payeer", "withdraw_type", "income")
    search_fields = ("id", "username", "status", "payeer")

    readonly_fields = ["date_payment"]

    fieldsets = (
        ("Money info", {
            "fields": ("payment_id", "payment_sum", "comission", "withdraw_type")
        }),

        ("Params", {
            "fields": ("payeer", "date_payment", "status")

        }),
    )


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about users of web interface 
    """
    list_display = ("id", "username", "verified_usr", "balance", "total_income")
    search_fields = ("id", "username")

    fieldsets = (
        ("Money info", {
            "fields": ("balance", "total_income")
        }),

        ("Params", {
            "fields": ("username", "telegram_id_in_admin_bot", "verified_usr", "is_superuser", "groups", "admin_info",)

        }),
    )

@admin.register(AdminApplication)
class AdminApplicationAdmin(admin.ModelAdmin):
    readonly_fields = ['date_created']

    list_display = ("id", "user", "status", "date_created")
    search_fields = ("id", "status", "application_number")

    fieldsets = (
        ("All fields", {
            "fields": ("user", "status", "date_created","application_number")

        }),
    )

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about telegram bots registered in web interface 
    """
    list_display = ("id", "name", "telegram_name", "income")
    search_fields = ("id", "name", "telegram_name",)

    fieldsets = (
        ("Bot params", {
            "fields": ("name", "token", "owner", "is_active", "telegram_name", "income")

        }),
    )


@admin.register(TGUser)
class TgUserAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about users registered in telegram bots 
    """
    list_display = ("telegram_id", "username",)
    search_fields = ("id", "telegram_id", "username",)

    fieldsets = (
        ("TgUser\"s main params", {
            "fields": (
                ("username"),
                "bot"
            )

       }),
    )

