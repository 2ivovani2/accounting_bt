from applier.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, re, random, io, shutil, validators
warnings.filterwarnings("ignore")

from PIL import Image

from django.core.management.base import BaseCommand
from django.conf import settings

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, File
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

@sync_to_async
def user_get_by_update(update: Update):
    
    """Функция обработчик, возвращающая django instance пользователя

    Returns:
        _type_: instance, created
    """

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if not message.chat.username:
        username = "Anonymous"
    else:
        username = message.chat.username

    instance, created = ApplyUser.objects.update_or_create(
        username = username,
        telegram_chat_id = message.chat.id,
    )
    
    return instance, created
    
class ApplierBot:
    
    def __init__(self) -> None:
        """"
            Инициализация апа
        """
        self.application = Application.builder().token(os.environ.get('APPLIER_BOT_TOKEN')).build()

    async def _start(self, update: Update, context: CallbackContext) -> None:
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🤩 <b>{usr.username}</b>, добрый день, если хотите отправить заявку на прием платежей, нажмите кнопку ниже.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Отправить заявку 🤘🏻",
                    callback_data="create_application",
                )]
            ])
        )

        return ConversationHandler.END
    

    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """
        self.application.add_handler(CommandHandler("start", self._start))

        return self.application

class Command(BaseCommand):
    help = 'Команда запуска TF MAKER BOT'

    def handle(self, *args, **kwargs):        
        main_class_instance = ApplierBot()
        application = main_class_instance.register_handlers()
        
        application.add_handler(CallbackQueryHandler(main_class_instance._start, "menu"))
        application.run_polling()