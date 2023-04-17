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
        self.bot_instance = telebot.TeleBot(self.token.strip(), parse_mode='HTML')
        self.bot_username = self.bot_instance.get_me().username

        return self.bot_username

    def start_telegram_bot_instance(self) -> None:
        """
            TODO create comments
        """
        
        def user_get_by_message(message, bot_username=self.bot_username):
            """
                Функция обработчик, возвращающая django instance пользователя
            """

            if not message.from_user.username:
                username = "NoName"
            else:
                username = message.from_user.username

            bot = Bot.objects.filter(telegram_name=bot_username).first()
            
            instance, created = TGUser.objects.update_or_create(
                telegram_id = message.from_user.id,
                username = username,
                bot=bot
            )

            return instance, created

        @self.bot_instance.message_handler(commands=['start'])
        def command_help(message):
            usr, _ = user_get_by_message(message)
            
            keyboard = telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton("🔎 Начать поиск", callback_data='start_search')],
                [telebot.types.InlineKeyboardButton("💶 Баланс", callback_data="balance_info")],
                [telebot.types.InlineKeyboardButton("💋 Отзывы", url="https://google.com")],
            ])
           
            
            self.bot_instance.send_photo(
                chat_id=usr.telegram_id,
                photo="https://sun9-31.userapi.com/impg/UMYV6G4oalcIesNyiYIl35blcDl5-PMWTDGBCQ/YsG3H_vYUxs.jpg?size=800x1550&quality=95&sign=5573c1012b27ea27f9af2fa89dd6c565&type=album",
                caption=f'👋 Привет, <b>{usr.username}</b>!\n\n🤖<b>Я - нейросеть, которая ищет приватные фото в тысячах баз по всему интернету.</b>\n\n🔎 Отправьте боту ссылку на старничку ВКонтакте, Instagram или FaceBook', 
                parse_mode="HTML", 
                reply_markup=keyboard
            )

        @self.bot_instance.message_handler(content_types=['text'], regexp='поиск')
        @self.bot_instance.callback_query_handler(lambda query: query.data == "start_search")
        def start_search_handler(message):
            usr, _ = user_get_by_message(message)

            keyboard = telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton("🌍 Вконтакте", callback_data="vk_search")],
                [telebot.types.InlineKeyboardButton("📞 Viber/Whats\'up", callback_data="phone_search")],
                [telebot.types.InlineKeyboardButton("📸 Инстаграм", callback_data="insta_search")],
            ])

            self.bot_instance.send_message(
                chat_id=usr.telegram_id,
                text=f"🤩 Отлично, давайте поищем!\n\n🆘Вы можете прислать боту запросы в следующем формате:\n\n🌍 <b>Вконтакте</b>\n├ https://vk.com/chapaevva\n└ vk.com/chapaevva\n\n📞 <b>Viber/Whats\'up</b>\n└ 79115553452\n\n📸 <b>Инстаграм</b>\n├ https://www.instagram.com/beyonce\n├ https://instagram.com/beyonce\n├ www.instagram.com/beyonce\n└ instagram.com/beyonce\n\n<i>Выберите подходящий способ поиска из списка ниже</i>",
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )

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

    balance = models.PositiveBigIntegerField(
        verbose_name='Telegram user\'s balance',
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
