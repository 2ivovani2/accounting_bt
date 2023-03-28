from bot_constructor.models import *

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand

import os, django, logging, warnings
warnings.filterwarnings("ignore")

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

VERIFIED_MARKUP = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Баланс 💰", callback_data="balance_info"),
            InlineKeyboardButton(text="Управление ботами 🤖", callback_data="bots_management")
        ],
        [
            InlineKeyboardButton(text="Статистика 📊", callback_data="statystic")
        ]
])

UNVERIFIED_MARKUP = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Регистрация 🐳", callback_data="verify"),
        ]
])


@sync_to_async
def user_get_by_update(update: Update):
    """
        Функция обработчик, возвращающая django instance пользователя
    """

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    instance, created = CustomUser.objects.update_or_create(
        telegram_id_in_admin_bot = message.chat.id,
        username = message.chat.username,
    )
    
    return instance, created

async def start(update: Update, context: CallbackContext) -> None:
    """
        Обработчик команды /start
    """
    usr, _ = await user_get_by_update(update)
    
    if usr.verified_usr:
        await context.bot.send_video(
            usr.telegram_id_in_admin_bot,
            "https://media1.giphy.com/media/G3Hu8RMcnHZA2JK6x1/giphy.gif?cid=ecf05e47qybjqyrdm7j9unlomb839p3w2u2mloamu2lcx5qu&rid=giphy.gif&ct=g",
            caption=f"С возвращением, <b>{usr.username}</b> 😽\nДанные обновлены 💼",
            parse_mode="HTML",
            reply_markup=VERIFIED_MARKUP
        )
    else:


        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"<b>{usr.username}</b>, вы не зарегистрированы в нашей системе 😳\n\nДля того, чтобы зарегистрироваться, необоходимо:\n\n🔴 <i>Нажать на кнопочку ниже</i>\n🔴 <i>Ответить на несколько вопросов</i>\n🔴 <i>Зарабатывать с нами</i>",
            parse_mode="HTML",
            reply_markup=UNVERIFIED_MARKUP
        )

async def verification(update: Update, context: CallbackContext) -> None:
    """
        Функция старта верификации
    """
    usr, _ = await user_get_by_update(update)

    if AdminApplication.objects.filter(user=usr, status="Created").exists():
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"В настоящее время вы уже отправили заявку на верификацию. 😶‍🌫️\nПожалуйста, дождитесь уведомления о решии админов.",
            parse_mode="HTML",      
        )

        return ConversationHandler.END

    await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"Уважаемый <b>{usr.username}</b>, необходимо предоставить следующие данные: \n\n<b>1)</b> Канал с вашими отзывами (если есть).\n\n<b>2)</b> Укажите аккаунты ваших знакомых, которые пользуются нашей ПП(Это не делает вас чьим-либо рефералом. Это проверка вас.)\n\n<b>3)</b> Укажите ссылки на ваши источники трафика (каналы, чаты, паблики и т.д.).\n\n<b>4)</b> Укажите, откуда вы узнали о нашей ПП.\n\n<b>Необходимо ответить максимально подробно.\nОтправляйте ответ одним сообщением</b>\n\n\nПубличный канал: @pp_dark_side",
            parse_mode="HTML",      
    )

    return 0

async def complete_verification(update: Update, context: CallbackContext) -> None:
    """
        Функция отправки данных админу и подтверждение или отклонение регистрации пользователя
    """

    usr, _ = await user_get_by_update(update)
    
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if not AdminApplication.objects.filter(user=usr).exists():
        AdminApplication(
            user=usr 
        ).save()

    accept_markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Принять ✅", callback_data="accept_usr"),
            InlineKeyboardButton(text="Отклонить ⛔️", callback_data="deny_usr"),
        ]
    ])

    admin = CustomUser.objects.filter(username="i_vovani").first()

    await context.bot.send_message(
        admin.telegram_id_in_admin_bot,
        f"Новая заявка на вступление:\n<b>{usr.telegram_id_in_admin_bot}</b>\n<b>{message.text}</b>",
        reply_markup=accept_markup,
        parse_mode="HTML"
    )
    
    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"📜 Ваша заявка отправлена на модерацию.\n\tПосле проверки вы получите уведомление.",
        parse_mode="HTML",      
    )

    return ConversationHandler.END

async def deny_user(update:Update, context:CallbackContext) -> None:
    """
        Функция отказывающая во вступлении в ПП
    """

    usr, _ = await user_get_by_update(update)
    
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if usr.is_superuser:
        new_user_id, _ = message.text.split("\n")[1:]
        
        if CustomUser.objects.filter(telegram_id_in_admin_bot=new_user_id).exists():
            new_usr = CustomUser.objects.filter(telegram_id_in_admin_bot=new_user_id)
            
            AdminApplication.objects.filter(
                user=new_usr[0]
            ).update(
                status="Denied"
            )

            await context.bot.send_message(
                new_usr[0].telegram_id_in_admin_bot,
                f"🥺 Уважаемый, <b>{new_usr[0].username}</b>!\nК сожалению, мы не можем добавить вас в нашу партнерскую программу. Можете попробовать еще раз.\n\nЕсли считаете, что произошла ошибка, обратитесь к @i_vovani",
                parse_mode="HTML",
                reply_markup=UNVERIFIED_MARKUP
            )

            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                "Отказ доставлен.",
            )

        else:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"К сожалению, пользователя с id={new_user_id} не существует. \n\nЕсли произошла ошибка, обратитесь к @i_vovani"
            )

    else:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"🙀 К сожалению, у вас недостаточно прав. Для совершения этой операции необходимы права администратора.\n\n Если произошла ошибка, обратитесь к @i_vovani",
            parse_mode="HTML",  
        )

async def accept_user(update:Update, context:CallbackContext) -> None:
    """
        Функция принимающая пользователя в ПП
    """
    usr, _ = await user_get_by_update(update)
    
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if usr.is_superuser:
        new_user_id, new_user_info = message.text.split("\n")[1:]
        
        if CustomUser.objects.filter(telegram_id_in_admin_bot=new_user_id).exists():
            new_usr = CustomUser.objects.filter(telegram_id_in_admin_bot=new_user_id)
            new_usr.update(
                verified_usr=True,
                admin_info=new_user_info
            )

            AdminApplication.objects.filter(
                user=new_usr[0]
            ).update(
                status="Accepted"
            )

            await context.bot.send_message(
                new_usr[0].telegram_id_in_admin_bot,
                f"🤩 Поздравляем, <b>{new_usr[0].username}</b>!\nВы были добавлены в нашу партнерскую программу. Успешных продаж!",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Открыть меню 📦", callback_data="main_menu"),
                ),
            )

            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                "Человек успешно принят.",
            )

        else:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"К сожалению, пользователя с id={new_user_id} не существует. \n\nЕсли произошла ошибка, обратитесь к @i_vovani"
            )

    else:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"🙀 К сожалению, у вас недостаточно прав. Для совершения этой операции необходимы права администратора.\n\n Если произошла ошибка, обратитесь к @i_vovani",
            parse_mode="HTML",  
        )

async def cancel(update: Update, context: CallbackContext) -> int:
    """
        Функция,  реализующая вызод из ConverstionHandler
    """
    usr, _ = await user_get_by_update(update)
    await update.message.reply_text(
        usr.telegram_id_in_admin_bot,
        ":(",
    )

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(os.environ.get("ADMIN_BOT_TOKEN")).build()
    
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(CallbackQueryHandler(start, "main_menu"))

    application.add_handler(CallbackQueryHandler(accept_user, "accept_usr"))
    application.add_handler(CallbackQueryHandler(deny_user, "deny_usr"))


    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(verification, "verify")],
        states={
            0: [MessageHandler(filters.TEXT, complete_verification)],
            
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    application.run_polling()


class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):        
        main()

        
        
        