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
            'fields': ('name', 'token', 'owner', 'functions')

        }),

        ('Social media params', {
            'fields': ('website', 'channel',),

        }),
    )


@admin.register(TGUser)
class TgUserAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about users registered in telegram bots 
    """
    list_display = ('telegram_id', 'ton_wallet', 'username',)
    search_fields = ('id', 'telegram_id', 'ton_wallet', 'username',)

    fieldsets = (
        ('TgUser\'s main params', {
            'fields': (
                ('telegram_id', 'ton_wallet'),
                ('username', 'is_admin'),
                'bot'
            )

       }),
        ('TgUser\'s additional params', {
            'fields':(
                'ref_token',
                'balance',
                'experience',
                'rank',
                'whitelisted',
                'messages_amount'
            )
        }

        )
    )


@admin.register(NFT)
class NFTAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about NFTS 
    """
    list_display = ('id', 'nft_name',)
    search_fields = ('id', 'nft_name',)

    fieldsets = (
        ('NFT\'s params', {
            'fields': (
                'nft_name',
                'nft_owner',
                'nft_creator',
            )

       }),
    )


@admin.register(ReferralLinks)
class ReferralLinksAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about Reffered links
    """
    list_display = ('id',)
    search_fields = ('id',)

    fieldsets = (
        ('Refferals\'s params', {
            'fields': (
                'referrer',
                'referred',
            )

       }),
    )

@admin.register(Function)
class FunctionsAdmin(admin.ModelAdmin):
    """
        Model describing how to display info about Functions
    """
    list_display = ('id', 'function_name')
    search_fields = ('id', 'function_name')

    fieldsets = (
        ('Function\'s params', {
            'fields': (
                'function_name',
                'function_desc',
                'function_sub',
            )

       }),
    )