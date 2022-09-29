from tabnanny import verbose
from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
        Model describing our website user's class
        @SUBSCRIPTION_CHOICES - variants of subscription
    """

    SUBSCRIPTION_CHOICES = (
        ('default','Default'),
        ('expanded', 'Expanded'),
        ('pro','Pro'),
    )

    ton_wallet = models.CharField(
        verbose_name='TON wallet address',
        max_length=255,
        null=False,
        default=False,
    )

    balance = models.PositiveIntegerField(
        verbose_name='Balance',
        null=False,
        default=0,
    )

    sub_type = models.CharField(
        verbose_name='Type of subscription',
        max_length=12,
        null=False,
        default='default',
        choices=SUBSCRIPTION_CHOICES, 
    )

    expiration_date = models.DateTimeField(
        verbose_name='Expiration date of subscription',
        null=True,
    )

    def __str__(self) -> str:
        return self.ton_wallet

    class Meta:
            verbose_name = 'Web user'
            verbose_name_plural = 'Web users'


class Function(models.Model):
    """
        Model describing functions of the bots
        @SUBSCRIPTION_CHOICES - variants of subscription

    """

    SUBSCRIPTION_CHOICES = (
        ('default','Default'),
        ('expanded', 'Expanded'),
        ('pro','Pro'),
    )

    function_name = models.CharField(
        verbose_name='Function name',
        max_length=50,
        null=False,
        default='none',
    )

    function_desc = models.TextField(
        verbose_name='Function description',
        null=False,
        default='none',
    )

    function_sub = models.CharField(
        verbose_name='Type of subscription',
        max_length=12,
        null=False,
        default='default',
        choices=SUBSCRIPTION_CHOICES, 
    )

    def __str__(self):
        return self.function_name

    class Meta:
            verbose_name = 'Function'
            verbose_name_plural = 'Functions'


class Bot(models.Model):
    """
        Model describing our website user's bots instances
    """

    token = models.CharField(
        verbose_name='TGBot token',
        max_length=150,
        null=False,
        default=False
    )

    name = models.CharField(
        verbose_name='TGBot name',
        max_length=100,
        null=False,
        default='Loly'
    )

    owner = models.ForeignKey(
        CustomUser,
        verbose_name='Bot owner',
        on_delete=models.CASCADE,
    )

    website = models.CharField(
        verbose_name='Project website link',
        max_length=255,
        null=True,
    )

    channel = models.CharField(
        verbose_name='Project channel link',
        max_length=255,
        null=True     
    )

    functions = models.ManyToManyField(
        Function,
        verbose_name='Functions included to bot'
    )

    def __str__(self):
        return self.name

    class Meta:
            verbose_name = 'Telegram Bot'
            verbose_name_plural = 'Telegram Bots'


class TGUser(models.Model):
    """
        Model describing current user's bot he belongs
    """
    
    telegram_id = models.PositiveBigIntegerField(
        verbose_name='Telegram user\'s id',
        null=False,
        default=0,
    )

    username = models.CharField(
        verbose_name='Telegram user\'s username',
        max_length=50,
        null=False,
        default='Ánonymous', 
    )

    is_admin = models.BooleanField(
        verbose_name='Bot admin status',
        null=False,
        default=False,
    )

    balance = models.PositiveIntegerField(
        verbose_name='Telegram user\'s balance',
        null=False,
        default=0,
    )

    experience = models.PositiveIntegerField(
        verbose_name='Telegram user\'s experience',
        null=False,
        default=0,
    )

    rank = models.CharField(
        verbose_name='Telegram user\'s rank',
        max_length=30,
        null=False,
        default='Vegetable',
    )

    ton_wallet = models.CharField(
        verbose_name='Telegram user\'s TON wallet address',
        max_length=255,
        null=False,
        default=False,
    )

    whitelisted = models.BooleanField(
        verbose_name='Telegram user\'s whitelist status',
        null=False,
        default=False,
    )

    messages_amount = models.PositiveIntegerField(
        verbose_name='Telegram user\'s messages amount',
        null=False,
        default=0,
    )

    ref_token = models.CharField(
        verbose_name='Telegram user\'s referral token',
        max_length=255,
        null=False,
        default='No token',
    )

    bot = models.ForeignKey(
        Bot,
        verbose_name='Telegram user\'s bot',
        on_delete=models.CASCADE,
    )
    
    def __str__(self) -> str:
        return self.username

    class Meta:
        verbose_name = 'Telegram User'
        verbose_name_plural = 'Telegram Users'


class NFT(models.Model):
    """
        Model describing nft
    """

    nft_name = models.CharField(
        verbose_name='NFT name',
        max_length=50,
        null=False,
        default='The best NFT in the world',
    )

    nft_creator = models.ForeignKey(
        TGUser,
        verbose_name='NFT creator',
        on_delete=models.CASCADE,
    )

    nft_owner = models.ForeignKey(
        CustomUser,
        verbose_name='NFT owner',
        on_delete=models.CASCADE,
    )

    def __str__(self) -> str:
        return self.nft_name

    class Meta:
        verbose_name = 'NFT'
        verbose_name_plural = 'NFTS'


class ReferralLinks(models.Model):
    """
        Model describing refferal links between users
    """

    referrer = models.ForeignKey(
        TGUser,
        verbose_name='Referrer user',
        related_name='referrer_user',
        on_delete=models.CASCADE
    )
    
    referred = models.ForeignKey(
        TGUser,
        verbose_name='Referred user',
        related_name='referred_user',
        on_delete=models.CASCADE
    )

    def __str__(self) -> str:
        return self.id

    class Meta:
        unique_together = (('referrer', 'referred'),)
        verbose_name = 'Referral link'
        verbose_name_plural = 'Referral links'
