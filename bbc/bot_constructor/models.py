from django.db import models
from django.contrib.auth.models import AbstractUser

import telebot, time, vk_api, pymorphy2, json, os, random, logging, uuid, re
from yookassa import Configuration, Payment

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


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

class TGPayment(models.Model):
    STATUS_CHOICES = (
        ("Проведен", "Проведен"),
        ("Создан", "Создан"),
    )

    amt = models.BigIntegerField(
        verbose_name="TGPayment amt",
        null=False,
        default=0
    )

    payment_id = models.CharField(
        verbose_name="TGPaymentID",
        max_length=255,
        null=False,
        default="No ID"
    )

    fact_amt = models.BigIntegerField(
        verbose_name="TGPayment fact amt",
        null=False,
        default=0
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        null=False,
        default="Создан",
    )
    
    owner = models.ForeignKey(
        CustomUser,
        verbose_name='Bot owner',
        on_delete=models.CASCADE,
        null=True
    )

    def __str__(self) -> str:
        return self.payment_id

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

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

    @staticmethod
    def create_payment(sum: int, return_url:str):
        Configuration.account_id = os.environ.get("SHOP_ID")
        Configuration.secret_key = os.environ.get("SHOP_API_TOKEN")

        payment = Payment.create({
            "amount": {
                "value": sum,
                "currency": "RUB"
            },

            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": 'Оплата информационных услуг.'
        })
        payment_data = json.loads(payment.json())
        payment_url = (payment_data['confirmation'])['confirmation_url']
        payment_id = payment_data['id']

        return payment_url, payment_id

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

        @self.bot_instance.callback_query_handler(lambda query: query.data == "menu")
        @self.bot_instance.message_handler(commands=['start'])
        def command_help(message):
            usr, _ = user_get_by_message(message)
            
            keyboard = telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton("🔎 Начать поиск", callback_data='search_choice')],
                [telebot.types.InlineKeyboardButton("💋 Отзывы", url="https://t.me/bikph")],
            ])
           
            
            self.bot_instance.send_photo(
                chat_id=usr.telegram_id,
                photo="https://sun9-31.userapi.com/impg/UMYV6G4oalcIesNyiYIl35blcDl5-PMWTDGBCQ/YsG3H_vYUxs.jpg?size=800x1550&quality=95&sign=5573c1012b27ea27f9af2fa89dd6c565&type=album",
                caption=f'👋 Привет, <b>{usr.username}</b>!\n\n🤖<b>Я - нейросеть, которая ищет приватные фото в тысячах баз по всему интернету.</b>\n\n🔎 Отправьте боту ссылку на старничку ВКонтакте, Instagram или FaceBook', 
                parse_mode="HTML", 
                reply_markup=keyboard
            )

        @self.bot_instance.message_handler(content_types=['text'], regexp='поиск')
        @self.bot_instance.callback_query_handler(lambda query: query.data == "search_choice")
        def search_choice_handler(message):
            usr, _ = user_get_by_message(message)

            keyboard = telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton("🌍 Вконтакте", callback_data="start_search")],
                [telebot.types.InlineKeyboardButton("📞 Viber/Whats\'up", callback_data="start_search")],
                [telebot.types.InlineKeyboardButton("📸 Инстаграм", callback_data="start_search")],
            ])

            self.bot_instance.send_message(
                chat_id=usr.telegram_id,
                text=f"🤩 Отлично, давайте поищем!\n\n🆘Вы можете прислать боту запросы в следующем формате:\n\n🌍 <b>Вконтакте</b>\n├ https://vk.com/chapaevva\n└ vk.com/chapaevva\n\n📞 <b>Viber/Whats\'up</b>\n└ 79115553452\n\n📸 <b>Инстаграм</b>\n├ https://www.instagram.com/beyonce\n├ https://instagram.com/beyonce\n├ www.instagram.com/beyonce\n└ instagram.com/beyonce\n\n<i>Выберите подходящий способ поиска из списка ниже</i>",
                parse_mode="HTML",
                reply_markup=keyboard,
                disable_web_page_preview=True
            )

        @self.bot_instance.callback_query_handler(lambda query: query.data == "start_search")
        def start_search(message):
            usr, _ = user_get_by_message(message)

            keyboard = telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton("📥 Меню", callback_data="menu")],
            ])


            self.bot_instance.send_message(
                chat_id=usr.telegram_id,
                text=f"💌 Хорошо, <b>{usr.username}</b>, отправь мне ссылку на пользователя.",
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        @self.bot_instance.message_handler(content_types=['text'], regexp="^\\+?[1-9][0-9]{7,14}$")
        @self.bot_instance.message_handler(content_types=['text'], regexp="((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*")  
        def link_valid(message):
            usr, _ = user_get_by_message(message)
            link = message.text.strip()
            
            if ("vk" in link):
                try:
                    vk_session = vk_api.VkApi(os.environ.get("VK_PHONE"), os.environ.get("VK_PASSWORD"))
                    vk_session.auth()

                    user = vk_session.method("users.get", {"user_ids": link.split("/")[-1]}) # вместо 1 подставляете айди нужного юзера
                    fn = user[0]['first_name']
                    
                    morph = pymorphy2.MorphAnalyzer()
                    parsed_word = morph.parse(fn)[0]
                    g = parsed_word.tag.gender
                    
                    if g.lower() != "femn":
                        self.bot_instance.send_message(
                            usr.telegram_id,
                            f"🥺 К сожалению, мы пока не ищем сливы мужчин.",
                            parse_mode="HTML"
                        )

                        return 

                except:
                    self.bot_instance.send_message(
                        usr.telegram_id,
                        f"🥺 К сожалению, ссылка прислана с ошибкой. Попробуйте еще раз.",
                        parse_mode="HTML"
                    )
                    return
            elif ("instagram" in link)  or re.match("^\\+?[1-9][0-9]{7,14}$", link.strip()):
                
                startin_text = list("🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥")
                msg = self.bot_instance.send_message(
                    usr.telegram_id,
                    f"Выполянем поиск... 🔎\n\n✅ Страница найдена в базе\n\n⏳ Отправка материала... <b>{0}%</b>\n{''.join(startin_text)}",
                    parse_mode="HTML"
                )

                for index in range(len(startin_text)):
                    startin_text[index] = "🟩"
                    self.bot_instance.edit_message_text(
                        f"Выполянем поиск... 🔎\n\n✅ Страница найдена в базе\n\n⏳ Отправка материала... <b>{(index + 1) * 10}%</b>\n{''.join(startin_text)}",
                        usr.telegram_id,
                        msg.id
                    )
                    time.sleep(0.5)
                
                
                payment399_url, payment399_id = Bot.create_payment(399, f'https://t.me/{self.bot_username}')
                payment199_url, payment199_id = Bot.create_payment(199, f'https://t.me/{self.bot_username}')

                TGPayment(
                    payment_id=payment399_id,
                    amt=399,
                    owner=self.owner
                ).save()
                
                TGPayment(
                    payment_id=payment199_id,
                    amt=199,
                    owner=self.owner
                ).save()


                kb = telebot.types.InlineKeyboardMarkup([
                    [telebot.types.InlineKeyboardButton("Приобрести 💳|199₽", url=str(payment199_url).strip())],
                    [telebot.types.InlineKeyboardButton("Купить безлимит 💳|399₽", url=str(payment399_url).strip())],
                    [telebot.types.InlineKeyboardButton("Проверить оплату ✅", callback_data="check_payment")],
                ])

                self.bot_instance.send_photo(
                    chat_id=usr.telegram_id,
                    photo="https://sun9-51.userapi.com/impg/LA8QLJqXNeiDAlF2ljlbyzAa4xE835jo6CZbEw/fUs8hTMKmIg.jpg?size=800x1550&quality=95&sign=127fdd19fa59b28301f2e325e6e5aa19&type=album",
                    caption=f"Слив найден ✅\n\n<b>Интим фото:</b>{random.randint(10, 50)} шт.\n<b>Интим видео:</b>{random.randint(1, 10)} шт.", 
                    parse_mode="HTML", 
                    reply_markup=kb
                )

                self.bot_instance.send_message(
                    usr.telegram_id,
                    parse_mode="HTML", 
                    reply_markup=kb
                )
            else:
                self.bot_instance.send_message(
                        usr.telegram_id,
                        f"🥺 К сожалению, ссылка прислана с ошибкой. Попробуйте еще раз.",
                        parse_mode="HTML"
                    )
                return

        @self.bot_instance.callback_query_handler(lambda query: query.data == "check_payment")
        def check_payment(message):
            usr, _ = user_get_by_message(message)
            keyboard = telebot.types.InlineKeyboardMarkup([
                [telebot.types.InlineKeyboardButton("📥 Меню", callback_data="menu")],
            ])

            self.bot_instance.send_message(
                chat_id=usr.telegram_id,
                text=f"😪 Оплата пока не прошла. Пожалуйста, подождите.",
                parse_mode="HTML",
                reply_markup=keyboard,
            )

        @self.bot_instance.message_handler()
        def garbage(message):
            self.bot_instance.send_message(message.chat.id, 'Я пока не знаю, как на такое реагировать! 🥺')

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

