from django.db import models
from django.contrib.auth.models import AbstractUser
import telebot

class CustomUser(AbstractUser):
    telegram_id_in_admin_bot = models.CharField(
        max_length=255,
        null=False,
        default="Can't find id", 
        verbose_name="Tg_id in admin bot"
    )

    verified_usr = models.BooleanField(
        verbose_name="Verified by admin",
        default=False
    )

    admin_info = models.TextField(
         verbose_name="Information of admin's work",
         null=False,
         default="No info"
    )

    balance = models.PositiveIntegerField(
        verbose_name='Balance',
        null=False,
        default=0,
    )

    total_income = models.PositiveBigIntegerField(
        verbose_name='Total income',
        null=False,
        default=0
    )

    def __str__(self) -> str:
        return self.username

    def to_dict(self) -> dict:
        return {
            'username':self.username,
            'balance':self.balance,
        }

    class Meta:
        verbose_name = 'Admin'
        verbose_name_plural = 'Admin'

class AdminApplication(models.Model):
    STATUS_CHOICES = (
        ("Принят", "Принят"),
        ("Отклонен", "Отклонен"),
        ("Создан", "Создан"),
    )

    date_created = models.DateTimeField(
        auto_now_add=True,
        blank=True, 
        verbose_name="Apply date"
    )

    user = models.ForeignKey(
        CustomUser,
        verbose_name="User, who sended an apply",
        on_delete=models.CASCADE
    )

    application_number = models.CharField(
        verbose_name="Application number",
        max_length=255,
        null=False,
        default="Not defined"
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        null=False,
        default="Создан",
    )

    def __str__(self) -> str:
        return self.user.username

    class Meta:
        verbose_name = 'Admin apply'
        verbose_name_plural = 'Admin applies'

class AdminTransaction(models.Model):
    STATUS_CHOICES = (
        ("В работе", "В работе"),
        ("Отменен", "Отменен"),
        ("Проведен", "Проведен"),
        ("Создан", "Создан"),
    )

    WITHDRAW_CHOICES = (
        ("Qiwi ник", "Qiwi ник"),
        ("Qiwi номер", "Qiwi номер"),
        ("Qiwi карта", "Qiwi карта"),
        ("ЮМани", "ЮМани"),
        ("Остальные карты", "Остальные карты"),
    )

    payment_id = models.CharField(
        verbose_name="id of payment",
        max_length=255,
        null=False,
        default="Not found"
    )

    withdraw_type = models.CharField(
        max_length=30,
        choices=WITHDRAW_CHOICES,
        null=False,
        default="Нет",
    )

    payment_sum = models.BigIntegerField(
        verbose_name="Sum of the payment",
        null=False,
        default=0,
    )

    date_payment = models.DateTimeField(
        auto_now_add=True,
        blank=True, 
        verbose_name="Apply date"
    )

    comission = models.BigIntegerField(
        verbose_name="Comission amt in %",
        null=False,
        default=0
    )

    status = models.CharField(
        verbose_name="Payment status",
        max_length=30,
        choices=STATUS_CHOICES,
        null=False,
        default="Создан",
    )

    payeer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="Person who applied for payment",
    )

    income = models.BigIntegerField(
        verbose_name="Income on apply",
        null=False,
        default=0
    )

    def __str__(self) -> str:
        return self.payeer.username

    class Meta:
        verbose_name = 'Admin transaction apply'
        verbose_name_plural = 'Admin transaction applies'

class Bot(models.Model):

    token = models.CharField(
        verbose_name='TGBot token',
        max_length=150,
        null=False,
        default=False
    )

    telegram_name = models.CharField(
        verbose_name="Telegram username",
        max_length=255,
        null=False,
        default="botfather"
    )

    name = models.CharField(
        verbose_name='TGBot name',
        max_length=100,
        null=False,
        default='Безымянный'
    )

    owner = models.ForeignKey(
        CustomUser,
        verbose_name='Bot owner',
        on_delete=models.CASCADE,
    )

    is_active = models.BooleanField(
        verbose_name='Bot activity status',
        null=False,
        default=False,
    )

    income = models.BigIntegerField(
        verbose_name="Total bot income",
        null=False,
        default=0
    )

    def __str__(self) -> str:
        return str(self.name)

    def create_telegram_instance(self) -> str:
        """
            TODO create comments
        """
        b = telebot.TeleBot(self.token.strip(), parse_mode='HTML')
        self.bot_instance = b

        return b.get_me().username
        
    def start_telegram_bot_instance(self) -> None:
        """
            TODO create comments
        """
        @self.bot_instance.message_handler(commands=['start', 'help'])
        def command_help(message):
            self.bot_instance.reply_to(message, "Hello, did someone call for help?")

        try:
            self.bot_instance.polling(none_stop=True)
        except Exception as e:
            return f"Error: {e}"
    
    class Meta:
        verbose_name = 'Telegram Bot'
        verbose_name_plural = 'Telegram Bots'

class TGUser(models.Model):
    
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
