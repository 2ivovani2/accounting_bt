from django.db import models
from django.contrib.auth.models import AbstractUser

import random


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


class Bot(models.Model):
    """
        Model describing our website user's bots instances
        # TODO Realise functions and many-to-many
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

    def __str__(self):
        return self.name

    class Meta:
            verbose_name = 'Telegram Bot'
            verbose_name_plural = 'Telegram Bots'


class TGUser(models.Model):
    """
        Model describing current user's bot he belongs
        # TODO Realise later
    """
    pass