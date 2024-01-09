from tf_maker.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, re, random, io, shutil
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

from PIL import Image
from tf_maker.generate_tf import TelegraphGenerator

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
        
        """Обработчик команды /start

        Returns:
            Завершает диалог, путем вызова ConversationHandler.END
        """

        usr, _ = await user_get_by_update(update)
        
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"😃 <b>{usr.username}</b>, добрый день, я бот для создания <pre>Telegraph</pre> постов.\n🤩 Нажмите кнопку ниже для его создания.",
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
    async def _ask_for_user_channel_link(update: Update, context: CallbackContext) -> int:

        """получение ссылки на канал пользователя

        Returns:
            стейт - 0
        """

        usr, _ = await user_get_by_update(update)

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🥰 Здравствуйте, пришлите, пожалуйста, <b>ССЫЛКУ</b> на ваш канал, где будет размещаться архив.",
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
    async def _ask_for_preview(update: Update, context: CallbackContext) -> int:

        """получение первой фотографии всего поста -- превью

        Returns:
            стейт - 1
        """

        usr, _ = await user_get_by_update(update)
        
        context.user_data["user_channel_link"] = update.message.text.strip()

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🤩 Отлично, <b>ссылку</b> я сохранил, теперь пришлите <b>фотографию</b> для превью, пожалуйста.\n\n👽 Или можете отправить все фото сразу, тогда первое <b>фото</b> будет взято в качестве <b>превью</b>.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Отмена 🍎",
                    callback_data="menu",
                )],
            ])
        )

        return 1

    @check_user_status
    async def _download_preview_and_ask_for_content(update: Update, context: CallbackContext) -> None:

        """загрузка превью на локальное хранилище и получение ботом второстепенных фото

        Returns:
            стейт - 2
        """

        usr, _ = await user_get_by_update(update)

        photo_id = update.message.photo[-1].file_id
        context.user_data["active_tf"] = photo_id

        file = await context.bot.get_file(photo_id)
        await file.download_to_drive(f"{photo_id}-preview.jpg")
        
        preview_img = Image.open(f"{photo_id}-preview.jpg")
        os.remove(f"{photo_id}-preview.jpg")

        os.mkdir(f"{settings.IMAGES_BASE_DIR}{photo_id}")
        os.mkdir(f"{settings.IMAGES_BASE_DIR}{photo_id}/content")
        
        preview_img.save(f"{settings.IMAGES_BASE_DIR}{photo_id}/preview.jpg", "JPEG")

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"😈 Отлично! <b>Превью</b> загружено, теперь отправьте фото для заполнения архива.",
            parse_mode = "HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Отмена 🍎",
                    callback_data="menu",
                )],
            ])
        )  

        return 2
    
    @check_user_status
    async def _download_content(update: Update, context: CallbackContext) -> None:

        """загрузка всех дополнительных фотографий на локальное хранилище(сервер)
        """

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

        content_img.save(f"{settings.IMAGES_BASE_DIR}{context.user_data['active_tf']}/content/{content_id}.jpg", "JPEG")
        
        message = await context.bot.send_message(
            usr.telegram_chat_id,
            f"🥵 Фото <b>{content_id}</b> загружено.\n\nЕсли вы хотите добавить еще фото для архива, просто отправьте их сюда, затем нажмите кнопку <pre>Создать Telegraph</pre>",
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
        """ создание телеграф-поста

        Args:
            update (Update): чтоб сообщеньки обновлять 
            context (CallbackContext): чтобы сделать send_message

        Returns:
            _type_: _description_
        """
        usr, _ = await user_get_by_update(update)

        telegraph_generator = TelegraphGenerator(
            access_token="9f18ea439b7f6620fe777e44a58108e4c3fe2090e659e0a3175e41e05445"
        )

        msg_about_starting = await context.bot.send_message(
            usr.telegram_chat_id,
            f"🥳 Начинаю создание <pre>Telegraph</pre>",
            parse_mode="HTML",
        )  

        try:
            telegraph_link = telegraph_generator._generate_html(
                preview_path=f"{settings.IMAGES_BASE_DIR}{context.user_data['active_tf']}/preview.jpg",
                content_dir=f"{settings.IMAGES_BASE_DIR}{context.user_data['active_tf']}/content/",
                user_channel_link=context.user_data["user_channel_link"],
                username=usr.username
            )

            Telegraph(
                creator=usr,
                link=telegraph_link
            ).save()

            shutil.rmtree(f"{settings.IMAGES_BASE_DIR}{context.user_data['active_tf']}", ignore_errors=True)
        
        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤬 Возникла ошибка во время создания <pre>Telegraph</pre> - <i>{e}</i>\n\nПожалуйста, свяжитесь с администратором и сообщите об этой ошибке, нажав на кнопку ниже.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Сообщить об ошибке ☎️",
                        url="https://t.me/i_vovani"
                    )]
                ])
            )  

        await context.bot.delete_message(
            usr.telegram_chat_id,
            msg_about_starting.id
        )

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🤩 <pre>Telegraph</pre> создан.\n🔗 <b>Ссылка:</b> {telegraph_link}",
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
                entry_points=[CommandHandler("create_tf", self._ask_for_user_channel_link), CallbackQueryHandler(self._ask_for_user_channel_link, "start_tf")],
                states={
                    0: [MessageHandler(filters.TEXT, self._ask_for_preview)],
                    1: [MessageHandler(filters.PHOTO, self._download_preview_and_ask_for_content)],
                    2: [MessageHandler(filters.PHOTO, self._download_content)],
                    
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