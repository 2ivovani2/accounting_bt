from tf_maker.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, re, random, io, shutil
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

from PIL import Image

from django.core.management.base import BaseCommand

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

IMAGES_BASE_DIR = "tf_maker/users_photo/"

@sync_to_async
def user_get_by_update(update: Update):
    """
        Функция обработчик, возвращающая django instance пользователя
    """

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if not message.chat.username:
        username = "Anonymous"
    else:
        username = message.chat.username

    instance, created = TFUser.objects.update_or_create(
        username = username,
        telegram_chat_id = message.chat.id,
    )
    
    return instance, created

def check_user_status(function):
    """
        Функция декоратор для проверки аутентификации пользователя
    """
    async def wrapper(self, update: Update, context:CallbackContext):   
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message

        if not message.chat.username:
            username = "Anonymous"
        else:
            username = message.chat.username

        usr, _ = TFUser.objects.update_or_create(
            telegram_chat_id = message.chat.id,
            username=username
        )

        if usr.verified_usr:
            return await function(update, context)
            
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"⛔️ <b>{usr.username}</b>, это приватный бот.\n\nДля того, чтобы им пользоваться нужно получить к нему доступ.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Запросить доступ 💅🏽",
                        url="https://t.me/i_vovani"
                    )]
                ])
        )
        
    return wrapper
    
class TFBot:
    
    def __init__(self) -> None:
        """"
            Инициализация апа
        """
        self.application = Application.builder().token(os.environ.get('TF_MAKER_BOT_TOKEN')).build()


    @check_user_status
    async def _start(update: Update, context: CallbackContext) -> None:
        """
            Обработчик команды /start

        """

        usr, _ = await user_get_by_update(update)
        
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"😃 <b>{usr.username}</b>, добрый день, я бот для создания <pre>Telegraph</pre> постов.\n\n🤩 Нажмите кнопку ниже для его создания.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать 🍭",
                    callback_data="start_tf",
                )],
            ])
        )

        return ConversationHandler.END
    
    @check_user_status
    async def _ask_for_preview(update: Update, context: CallbackContext) -> int:
        usr, _ = await user_get_by_update(update)
        
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🥰 Здравствуйте, пришлите фотографию для превью, пожалуйста.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Отмена 🍎",
                    callback_data="menu",
                )],
            ])
        )

        return 0

    @check_user_status
    async def _download_preview_and_ask_for_content(update: Update, context: CallbackContext) -> None:
        usr, _ = await user_get_by_update(update)

        photo_id = update.message.photo[-1].file_id
        context.user_data["active_tf"] = photo_id

        file = await context.bot.get_file(photo_id)
        await file.download_to_drive(f"{photo_id}-preview.jpg")
        
        preview_img = Image.open(f"{photo_id}-preview.jpg")
        os.remove(f"{photo_id}-preview.jpg")

        os.mkdir(f"{IMAGES_BASE_DIR}{photo_id}")
        os.mkdir(f"{IMAGES_BASE_DIR}{photo_id}/content")
        
        preview_img.save(f"{IMAGES_BASE_DIR}{photo_id}/preview.jpg", "JPEG")

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"😈 Отлично! Превью загружено, теперь отправьте фото для заполнения архива.",
            parse_mode = "HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Отмена 🍎",
                    callback_data="menu",
                )],
            ])
        )  

        return 1
    
    @check_user_status
    async def _download_content(update: Update, context: CallbackContext) -> None:
        usr, _ = await user_get_by_update(update)
        content_id = update.message.photo[-1].file_id

        if context.user_data.get("message_id", None) != None:
            await context.bot.delete_message(
                usr.telegram_chat_id,
                context.user_data["message_id"]
            )

        file = await context.bot.get_file(content_id)
        await file.download_to_drive(f"{content_id}.jpg")
        
        content_img = Image.open(f"{content_id}.jpg")
        os.remove(f"{content_id}.jpg")

        content_img.save(f"{IMAGES_BASE_DIR}{context.user_data['active_tf']}/content/{content_id}.jpg", "JPEG")
        
        message = await context.bot.send_message(
            usr.telegram_chat_id,
            f"🥵 Фото <b>{content_id}</b> загружено.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать Telegraph 🚨",
                    callback_data="create_tf",
                )],
                [InlineKeyboardButton(
                    text="Отмена 🍎",
                    callback_data="menu",
                )],
            ])
        )  

        context.user_data["message_id"] = message.id
        
    @check_user_status
    async def _create_telegraph(update: Update, context: CallbackContext) -> None:
        usr, _ = await user_get_by_update(update)

        shutil.rmtree(f"{IMAGES_BASE_DIR}{context.user_data['active_tf']}", ignore_errors=True)
        
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🤩 <pre><b>Telegraph</b></pre> создан.\n\n🔗 <b>Ссылка:</b> https://google.com",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍎",
                    callback_data="menu",
                )],
            ])
        )  
        return ConversationHandler.END

    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """
        self.application.add_handler(CommandHandler("start", self._start))
        self.application.add_handler(ConversationHandler(
                entry_points=[CommandHandler("create_tf", self._ask_for_preview), CallbackQueryHandler(self._ask_for_preview, "start_tf")],
                states={
                    0: [MessageHandler(filters.PHOTO, self._download_preview_and_ask_for_content)],
                    1: [MessageHandler(filters.PHOTO, self._download_content)],
                    
                },
                fallbacks=[CommandHandler("start", self._start), CallbackQueryHandler(self._create_telegraph, "create_tf"), CallbackQueryHandler(self._start, "menu")]
            )
        )

        return self.application

class Command(BaseCommand):
    help = 'Команда запуска TF MAKER BOT'

    def handle(self, *args, **kwargs):        
        main_class_instance = TFBot()
        application = main_class_instance.register_handlers()
        
        application.add_handler(CallbackQueryHandler(main_class_instance._start, "menu"))
        application.run_polling()