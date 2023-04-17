import telebot

from .models import *
from rest_framework.authtoken.models import Token

class BotTemplate:

    def __init__(self, bot_instance, bot_username):
        self.bot_instance = bot_instance
        self.bot_username = bot_username

    def user_get_by_message(self, message):
        """
            Функция обработчик, возвращающая django instance пользователя
        """

        if not message.chat.username:
            username = "NoName"
        else:
            username = message.chat.username

        instance, created = TGUser.objects.update_or_create(
            telegram_id = message.chat.id,
            username = username,
            bot=Bot.objects.filter(name=self.bot_username).first()
        )

        token = Token.objects.get_or_create(user=instance)
        
        return instance, created, token[0].key
    
    def init_functions(self):
        @self.bot_instance.message_handler(commands=['start', 'help'])
        def command_help(self, message):
            usr, _, _ = self.user_get_by_message(message)

            self.bot_instance.send_message(
                usr.telegram_id,
                f'{usr.username}, how are you?'
            )
            
        return self.bot_instance