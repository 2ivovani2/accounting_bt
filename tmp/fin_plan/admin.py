from django.contrib import admin
from fin_plan.models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
        Описание пользователей в админской панели
    """
    list_display = ("id", "username", "verified_usr", "type", "invite_code_limits")
    search_fields = ("id", "username", "type")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["username", "telegram_chat_id", "verified_usr", "can_create_tasks", "type", "invite_code_limits"]

        }),
    )

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """
        Описание проектов в админской панели
    """
    list_display = ("id", "name", "creator")
    search_fields = ("id", "name")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["name", "creator", "users"]

        }),
    )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
        Описание задач в админской панели
    """
    list_display = ("id", "name", "responsible", "deadline")
    search_fields = ("id", "name")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["name", "description", "responsible", "task_creator", "deadline"]

        }),
    )

@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    """
        Описание задач в админской панели
    """
    list_display = ("id", "code", "activator", "valid", "invite_type", "project")
    search_fields = ("id", "code", "invite_type")

    fieldsets = (

        ("Основные параметры", {
            "fields": ["code", "creator", "activator", "valid", "invite_type", "project"]

        }),
    )
