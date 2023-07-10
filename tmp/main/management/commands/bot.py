from main.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings
warnings.filterwarnings("ignore")

from django.core.management.base import BaseCommand

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
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

    instance, created = CustomUser.objects.update_or_create(
        username = username,
        telegram_chat_id = message.chat.id,
    )

    token = Token.objects.get_or_create(user=instance)
    
    return instance, created, token[0].key

async def start(update: Update, context: CallbackContext) -> None:
    """
        Обработчик команды /start
    """
    usr, _, _ = await user_get_by_update(update)
    
    if usr.verified_usr:
        if context.user_data.get("active_table_id", "") in [tbl.id for tbl in usr.get_tables()]:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать новую таблицу ➕",
                    callback_data="create_table",
                )],
                [InlineKeyboardButton(
                    text="Добавить операцию в активную таблицу 💸",
                    callback_data="add_operation",
                )],
                [InlineKeyboardButton(
                    text="Список моих таблиц 📃",
                    callback_data="list_table",
                )]
            ])

        else:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать новую таблицу ➕",
                    callback_data="create_table",
                )],
                [InlineKeyboardButton(
                    text="Список моих таблиц 📃",
                    callback_data="list_table",
                )]
            ])

        await context.bot.send_video(
            usr.telegram_chat_id,
            "https://media2.giphy.com/media/67ThRZlYBvibtdF9JH/giphy.gif?cid=ecf05e47u0hkmcznkfg7hju8bo77hffom4asrl76jmv4xlpd&ep=v1_gifs_search&rid=giphy.gif&ct=g",
            caption=f"😽 С возвращением, <b>{usr.username}</b>\n💰 Уже подсчитываю ваши миллионы",
            parse_mode="HTML",
            width=150,
            height=150,
            reply_markup=markup
        )
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

    return ConversationHandler.END

async def ask_for_table_name(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)

    if usr.can_create_tables:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🖍 Напишите название для вашей новой таблицы.\n\n<i>Максимальная длина - 12 символов</i>",
            parse_mode="HTML",
        )

        return 0
    
    else:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"⛔️ <b>{usr.username}</b>, у вас недостаточно прав для создания новых таблиц.\n\nВы можете запросить доступ на создание по ссылке ниже.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Запросить доступ 💅🏽",
                    url="https://t.me/i_vovani"
                )]
            ])
        )

        return ConversationHandler.END

async def create_table(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)

    try:
        if len(update.message.text) > 12:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"👿 Допустимное количесвто символов превышено.\n\nМаксимум - <b>12</b>\nУ вас - <b>{len(update.message.text)}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="start"
                    )]
                ])
            )

            return None

        new_table = Table(
            name=update.message.text
        )
        new_table.save()
        usr.tables.add(new_table)

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"✅ Таблица <b>{new_table.name.capitalize()}</b> успешно создана",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Добавить запись 🏧",
                    callback_data="ask_for_note_type"
                )]
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="start"
                )]
            ])
        )

    except Exception as e:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"❌ Что-то не так. Таблица <b>{new_table.name.capitalize()}</b> не создана.\n\n<b>Ошибка:</b><i>{e}</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="start"
                )]
            ])
        )

async def list_table(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    
    user_tables = list(reversed(usr.get_tables()))

    if len(user_tables) != 0:
        msg = ""
        reply_keyboard = []
        for table in user_tables:
            msg += f"<b>ID</b> - {table.id}{' ' * (4 - len(str(table.id)))} <b>Название</b> - {table.name}{' ' * (12 - len(table.name))}\n"
            reply_keyboard.append([KeyboardButton(text=f"ID - {table.id} {table.name}")])

        await context.bot.send_message(
                usr.telegram_chat_id,
                f"👺 <b>{usr.username}</b>, вот все ваши таблицы:\n\n{msg}",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
            )
        
        return 0

    else:
        await context.bot.send_message(
                usr.telegram_chat_id,
                f"💩 <b>{usr.username}</b>, у вас пока нет ни одной таблицы, попробуйте создать по кнопке ниже.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать новую таблицу ➕",
                    callback_data="create_table",
                )],
              ])
            )

        return ConversationHandler.END

async def choose_table(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    
    try:
        id = int(update.message.text.split()[2])
        print(id)

        if id in [tbl.id for tbl in usr.get_tables()]:
            context.user_data["active_table_id"] = id

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤖 Вы выбрали таблицу с id = {id}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Добавить операцию 💸",
                        callback_data="add_operation",
                    )],
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="start"
                    )]
                ])
            )

        else:
            await context.bot.send_message(
            usr.telegram_chat_id,
            f"❌ Что-то не так.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="start"
                )]
            ])
        )

    except Exception as e:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"❌ Что-то не так.\n\n<b>Ошибка:</b><i>{e}</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="start"
                )]
            ])
        )

    return ConversationHandler.END

def main() -> None:
    """
        Запуск бота
    """
    application = Application.builder().token(os.environ.get("ACCOUNT_BOT_TOKEN")).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start, "start")) 
    

    create_table_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_table_name, "create_table")],
        states={
            0: [MessageHandler(filters.TEXT, create_table)],
        },
        fallbacks=[]
    )
    application.add_handler(create_table_conv_handler)

    choose_table_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(list_table, "list_table")],
        states={
            0: [MessageHandler(filters.TEXT, choose_table)],
        },
        fallbacks=[]
    )
    application.add_handler(choose_table_conv_handler)


    application.run_polling()


class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):        
        main()

        
        
        
