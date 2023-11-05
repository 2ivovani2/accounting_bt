from django.contrib import admin
from main.models import *

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "username", "verified_usr")
    search_fields = ("id", "username")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["username", "telegram_chat_id", "verified_usr", "is_superuser", "can_create_tables"]

        }),

        ("Таблицы пользователя", {
            "fields": ["tables"]

        }),
    )
	
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "name", "type", "table")
    search_fields = ("id", "name", "table", "type")

    fieldsets = (

        ("Информация", {
            "fields": ["name", "table", "type"]

        }),

    )

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    """
        Описание таблиц в админской панели
    """
    list_display = ("id", "name")
    search_fields = ("id", "name")

    readonly_fields = ["id"]

    fieldsets = (

        ("Основные параметры", {
            "fields": ["name"]
        }),
    )

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    """
        Описание операций в админской панели 
    """
    list_display = ("id", "type", "amount", "date", "table", "category")
    search_fields = ("id", "type", "amount", "date", "description", "table__name")

    readonly_fields = ["id", "date"]

    fieldsets = (
        ("Основные параметры", {
            "fields": ["type", "amount", "table", "creator", "description","category"]
        }),
    )
