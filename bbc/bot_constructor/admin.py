from django.contrib import admin
from bot_constructor.models import *

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about users of web interface 
    """
    list_display = ('id', 'ton_wallet', 'sub_type', 'expiration_date', 'is_superuser')
    search_fields = ('id', 'ton_wallet', )

    fieldsets = (
        ('Custom params', {
            'fields': ('ton_wallet', ('password', 'username'), ('sub_type', 'expiration_date'), 'is_superuser', 'groups')

        }),
    )

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about telegram bots registered in web interface 
    """
    list_display = ('id', 'name', 'token',)
    search_fields = ('id', 'name', 'token',)

    fieldsets = (
        ('Bot params', {
            'fields': ('name', 'token', 'owner', )

        }),
    )