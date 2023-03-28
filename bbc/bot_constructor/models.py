from django.db import models
from django.contrib.auth.models import AbstractUser


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
        ("Accepted", "Accepted"),
        ("Denied", "Denied"),
        ("Created", "Created"),
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

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        null=False,
        default="Created",
    )

    def __str__(self) -> str:
        return self.user.username

    class Meta:
        verbose_name = 'Admin apply'
        verbose_name_plural = 'Admin applies'

class Bot(models.Model):

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

    is_active = models.BooleanField(
        verbose_name='Bot activity status',
        null=False,
        default=False,
    )

    def __str__(self) -> str:
        return str(self.name)

    # def create_telegram_instance(self) -> None:
    #     """
    #         TODO create comments
    #     """
    #     self.bot_instance = telebot.TeleBot(self.token.strip(), parse_mode='HTML')
        
    # def start_telegram_bot_instance(self) -> None:
    #     """
    #         TODO create comments
    #     """
    #     @self.bot_instance.message_handler(commands=['start', 'help'])
    #     def command_help(message):
    #         self.bot_instance.reply_to(message, "Hello, did someone call for help?")

    #     self.bot_instance.polling(none_stop=True)


    def to_dict(self) -> dict:
        opts = self._meta
        data = {
            'bot_token':self.token,
            'bot_name':self.name,
        }

        for f in opts.many_to_many:
            data[f.name] = [i.function_name for i in f.value_from_object(self)]
        
        return data
    
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
