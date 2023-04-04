from django.contrib import admin
from bot_constructor.models import *


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
    search_fields = ("id", "status")


    fieldsets = (
        ("All fields", {
            "fields": ("user", "status", "date_created",)

        }),
    )

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about telegram bots registered in web interface 
    """
    list_display = ("id", "name", "token",)
    search_fields = ("id", "name", "token",)

    fieldsets = (
        ("Bot params", {
            "fields": ("name", "token", "owner", "is_active")

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

