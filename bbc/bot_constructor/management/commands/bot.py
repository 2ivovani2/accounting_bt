from bot_constructor.models import *

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, requests, uuid
warnings.filterwarnings("ignore")

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

VERIFIED_MARKUP = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Управление ботами 🤖", callback_data="bots_management")
        ],
        [
            InlineKeyboardButton(text="Статистика 📊", callback_data="stat")
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

    if not message.chat.username:
        username = "NoName"
    else:
        username = message.chat.username

    instance, created = CustomUser.objects.update_or_create(
        telegram_id_in_admin_bot = message.chat.id,
        username = username,
    )

    token = Token.objects.get_or_create(user=instance)
    
    return instance, created, token[0].key

async def start(update: Update, context: CallbackContext) -> None:
    """
        Обработчик команды /start
    """
    usr, _, _ = await user_get_by_update(update)
    
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
            f"<b>{usr.username}</b>, вы не зарегистрированы в нашей системе 😳\n\nДля того, чтобы зарегистрироваться, необходимо:\n⚫ <i>Нажать на кнопочку ниже</i>\n⚫ <i>Ответить на несколько вопросов</i>\n⚫ <i>Ожидать ответ администратора</i>",
            parse_mode="HTML",
            reply_markup=UNVERIFIED_MARKUP
        )

    return ConversationHandler.END

async def verification(update: Update, context: CallbackContext) -> None:
    """
        Функция старта верификации
    """
    usr, _, _ = await user_get_by_update(update)

    if AdminApplication.objects.filter(user=usr, status="Created").exists():
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"В настоящее время вы уже отправили заявку на верификацию. 😶‍🌫️\nПожалуйста, дождитесь уведомления о решии админов.",
            parse_mode="HTML",      
        )

        return ConversationHandler.END

    await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"Уважаемый <b>{usr.username}</b>, необходимо предоставить следующие данные: \n\n<b>1)</b> Источники вашего трафика( Тикток, Телеграм, ВК, Другое )\n\n<b>2)</b> Укажите откуда вы узнали о нашей ПП (Это не делает вас чьим-либо рефералом.)\n\n<b>3)</b> Канал с вашими отзывами (При наличии)\n\n<b>4)</b> Ссылки на ваши источники трафика(телеграм каналы, тикток аккаунты, чаты, группы ВК и т.д.)\n\nПри необходимости саппорт вправе потребовать от вас док-во владения тем или иным источником трафика.\n\nОтвет отправлять <b>СТРОГО</b> одним сообщением. \n\n\nПубличный канал: @pp_dark_side\nЗадать вопрос: @i_vovani",
            parse_mode="HTML",      
    )

    return 0

async def complete_verification(update: Update, context: CallbackContext) -> ConversationHandler.END:
    """
        Функция отправки данных админу и подтверждение или отклонение регистрации пользователя
    """

    usr, _, _ = await user_get_by_update(update)
    
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    application_id = str(uuid.uuid4())[:8]
    application = AdminApplication(
        user=usr,
        application_number=application_id
    )
    application.save()
        
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
        f"⚫️ Ваша заявка отправлена на одобрение.\n\n⬛️ Номер заявки: <b>{application.application_number}</b>\n\nОжидайте подключения.\nЕсли возникнут вопросы: @i_vovani",
        parse_mode="HTML",      
    )

    return ConversationHandler.END

async def deny_user(update:Update, context:CallbackContext) -> None:
    """
        Функция отказывающая во вступлении в ПП
    """

    usr, _, _ = await user_get_by_update(update)
    
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if usr.is_superuser:
        new_user_id, _ = message.text.split("\n")[1:]
        
        if CustomUser.objects.filter(telegram_id_in_admin_bot=new_user_id).exists():
            new_usr = CustomUser.objects.filter(telegram_id_in_admin_bot=new_user_id).first()
            
            application = AdminApplication.objects.filter(
                user=new_usr
            )
            application.update(
                status="Отклонен"
            )

            await context.bot.delete_message(
                usr.telegram_id_in_admin_bot,
                update.effective_message.id
            )
            
            await context.bot.send_message(
                new_usr.telegram_id_in_admin_bot,
                f"✖ К сожалению, ваша заявка <b>{application.first().application_number}</b> была отклонена\nПопробуйте еще раз, либо обратитесь к администратору\n\nАдминистратор: @i_vovani ",
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
    usr, _, _ = await user_get_by_update(update)
    
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

            application = AdminApplication.objects.filter(
                user=new_usr[0]
            )
            application.update(
                status="Принят"
            )

            await context.bot.delete_message(
                usr.telegram_id_in_admin_bot,
                update.effective_message.id
            )

            await context.bot.send_message(
                new_usr[0].telegram_id_in_admin_bot,
                f"Вы успешно подключены ✅\n\nУдачного пользования ботом\nАдмин: @i_vovani\nОткрытый канал: @pp_dark_side\n",
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

async def ask_for_bot_name(update:Update, context:CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    
    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"🤖 <b>{usr.username}</b>, отправьте сюда, то как бы вы назвали своего бота.",
        parse_mode="HTML"
    )

    return 0

async def ask_for_bot_token(update:Update, context:CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    
    if len(Bot.objects.filter(owner=usr).all()) == int(os.environ.get("BOTS_LIMIT")):
        context.bot.send_message(
            usr.telegram_id_in_admin_bot, 
            f"<b>{usr.username}</b>, вы превысили лимит на создание ботов.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )
        
        return ConversationHandler.END

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    context.user_data["perm_bot_name"] = message.text

    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"👍🏼 Отлично! Теперь отправьте сюда <b>токен</b> вашего бота,\nполученный от <b>@BotFather</b>",
        parse_mode="HTML"
    )

    return 1

async def create_bot_by_usr_token(update:Update, context:CallbackContext):
    usr, _, auth_token = await user_get_by_update(update)
   
    message = update.message

    if Bot.objects.filter(token=message.text.strip()).exists():
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"❌ Бот с данным токеном уже существует.",
        )
    
        return ConversationHandler.END

    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"👁 Бот создается",
    )
    
    headers = {
        "Authorization":"Token " + auth_token,
    }

    data = {
        "bot_token":message.text.strip(),
        "bot_name":context.user_data["perm_bot_name"]
    }

    if not os.environ.get("API_PORT"):
        r = requests.post(f'{os.environ.get("API_PROTOCOL")}://{os.environ.get("API_HOST")}/api/constructor/create_bot', headers=headers, data=data)
    else:
        r = requests.post(f'{os.environ.get("API_PROTOCOL")}://{os.environ.get("API_HOST")}:{os.environ.get("API_PORT")}/api/constructor/create_bot', headers=headers, data=data)

    if r.status_code == 200:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"🤩 Успех! Ваш бот уже работает и приносит вам деньги.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )
    else:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"😔 К сожалению, не удалось захостить вашего бота.\n\n<b>Ошибка</b>:\n{r.json()['text']}\n\nЕсли ошибка возникает не в первый раз, обратитесь к @i_vovani",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )
    
    return ConversationHandler.END

async def user_bots_info(update:Update, context:CallbackContext) -> None:
    usr, _, _ = await user_get_by_update(update)
    user_bots = Bot.objects.filter(owner=usr).all()


    if len(user_bots) == 0:
        zero_bots_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="Создать бота ➕", callback_data="create_bot_for_admin")
            ]
        ])

        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"😔 <b>{usr.username}</b>, у вас пока нет ни одного бота.\n\nЕсли хотите создать бота, то нажмите кнопку ниже.",
            parse_mode="HTML",
            reply_markup=zero_bots_keyboard
        )

    else:
        not_zero_bots_keyboard = [
            [InlineKeyboardButton(text="Создать бота ➕", callback_data="create_bot_for_admin")]
        ]

        end_message = f"👀 <b>{usr.username}</b>, у вас <b>{len(user_bots)}</b> ботов.\nИнформация по ним представлена ниже:\n\n"

        for bot in user_bots:
            end_message += f"🆔: <b>{bot.id}</b>\n🍅 Юзернейм: <b>@{bot.telegram_name}</b>\n👩🏼‍💻Имя в базе: <b>{bot.name}</b>\n"

            if bot.is_active:
                end_message += "✅ Статус работы: <b>работает</b>"
                not_zero_bots_keyboard.append(
                    [InlineKeyboardButton(text=f"Остановить бота 📌{bot.id}📌", callback_data=f"stop_bot_{bot.id}")]
                )
            else:
                end_message += "❌ Статус работы: <b>отключен</b>"
                not_zero_bots_keyboard.append(
                    [InlineKeyboardButton(text=f"Активировать бота 📌{bot.id}📌", callback_data=f"activate_bot_{bot.id}")]
                )

        end_message += "\n\n"
        not_zero_bots_keyboard.append(
            [InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu")]
        )

        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            end_message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(not_zero_bots_keyboard)
        )

async def stop_activate_bot(update:Update, context:CallbackContext):
    usr, _, auth_token = await user_get_by_update(update)
    q = update.callback_query.data.split("_")

    if q[0] + "_" + q[1] == "activate_bot" and Bot.objects.get(pk=q[2]) != None:
        bot_by_id = Bot.objects.get(pk=q[2])
        
        if bot_by_id.owner == usr and not bot_by_id.is_active:
            headers = {
                "Authorization":"Token " + auth_token,
            }

            data = {
                "bot_token":bot_by_id.token,
            }
            
            if not os.environ.get("API_PORT"):
                r = requests.post(f'{os.environ.get("API_PROTOCOL")}://{os.environ.get("API_HOST")}/api/constructor/start_bot', headers=headers, data=data)
            else:
                r = requests.post(f'{os.environ.get("API_PROTOCOL")}://{os.environ.get("API_HOST")}:{os.environ.get("API_PORT")}/api/constructor/start_bot', headers=headers, data=data)

           
            if r.status_code == 200:
                bot_by_id.is_active = True
                bot_by_id.save()

                await context.bot.delete_message(
                    usr.telegram_id_in_admin_bot,
                    update.effective_message.id
                )

                await context.bot.send_message(
                    usr.telegram_id_in_admin_bot,
                    f"🤩 Успех! Вы запустили своего ботика.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup.from_button(
                            InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                    ),
                )
            else:
                await context.bot.send_message(
                    usr.telegram_id_in_admin_bot,
                    f"😔 К сожалению, не удалось запустить вашего бота.\n\n<b>Ошибка</b>:\n{r.json()['text']}\n\nЕсли ошибка возникает не в первый раз, обратитесь к @i_vovani",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup.from_button(
                            InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                    ),
                )


        else:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"<b>{usr.username}</b>, возникла ошибка с <i>callback</i>.\n\nОбратитесь к @i_vovani",
                parse_mode="HTML", 
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )

    elif q[0] + "_" + q[1] == "stop_bot" and Bot.objects.get(pk=q[2]) != None:
        bot_by_id = Bot.objects.get(pk=q[2])
        
        if bot_by_id.owner == usr:
            headers = {
                "Authorization":"Token " + auth_token,
            }

            data = {
                "bot_token":bot_by_id.token,
            }

            if not os.environ.get("API_PORT"):
                r = requests.post(f'{os.environ.get("API_PROTOCOL")}://{os.environ.get("API_HOST")}/api/constructor/stop_bot', headers=headers, data=data)
            else:
                r = requests.post(f'{os.environ.get("API_PROTOCOL")}://{os.environ.get("API_HOST")}:{os.environ.get("API_PORT")}/api/constructor/stop_bot', headers=headers, data=data)

            if r.status_code == 200:
                bot_by_id.is_active = False
                bot_by_id.save()

                await context.bot.delete_message(
                    usr.telegram_id_in_admin_bot,
                    update.effective_message.id
                )

                await context.bot.send_message(
                    usr.telegram_id_in_admin_bot,
                    f"🤩 Успех! Вы остановили своего ботика.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup.from_button(
                            InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                    ),
                )
            else:
                await context.bot.send_message(
                    usr.telegram_id_in_admin_bot,
                    f"😔 К сожалению, не удалось остановить вашего бота.\n\n<b>Ошибка</b>:\n{r.json()['text']}\n\nЕсли ошибка возникает не в первый раз, обратитесь к @i_vovani",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup.from_button(
                            InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                    ),
                )

        else:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"<b>{usr.username}</b>, возникла ошибка с <i>callback</i>.\n\nОбратитесь к @i_vovani",
                parse_mode="HTML", 
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )
    
        
    else:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"<b>{usr.username}</b>, возникла ошибка с <i>callback</i>.\n\nОбратитесь к @i_vovani",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )

async def stat(update:Update, context:CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    user_bots = Bot.objects.filter(owner=usr).all()
    end_message = f"💰 Актуальный баланс: <b>{usr.balance}₽</b>\n📊 Суммарный оборот: <b>{usr.total_income}₽</b>"

    if len(user_bots) != 0:
        end_message += "\n\n🤖 <b>Статистика по ботам:</b>\n\n"
        for bot in user_bots:
            end_message += f"🍅 Юзернейм: <b>@{bot.telegram_name}</b>\n💲 Прибыль: <b>{bot.income}₽</b>"

    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        end_message,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="Создать выплату 💷", callback_data="create_withdraw"),
            ],
        
            [
                InlineKeyboardButton(text="Список выплат 🖇", callback_data="withdraw_list"),
            ],
        
            [
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ],
        ])
    )

async def ask_for_payment_method(update:Update, context:CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    
    await context.bot.delete_message(
        usr.telegram_id_in_admin_bot,
        update.effective_message.id
    )

    if usr.balance > (50 / 0.9): 
        cards_amt_avaliable = usr.balance * 0.9 - 50 
    else: 
        cards_amt_avaliable = usr.balance * 0.9
    
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton(text="🥝 Qiwi ник"), KeyboardButton(text="🥝 Qiwi номер")],
        [KeyboardButton(text="🥝 Qiwi карта"), KeyboardButton(text="💳 Остальные карты")],
        [KeyboardButton(text="🟪 ЮМани")]  
    ], one_time_keyboard=True, resize_keyboard=True)

    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"<b>⬛️ Комиссия банков:</b>\n\n🥝<b>3%</b> QIWI (Карта, Номер, Ник)\n🟪 <b>3%</b> ЮMoney\n💳 <b>3% + 50р</b> - Остальные карты\n\n<b>⬛️ Доступно (с учетом комиссии):</b>\n🟪 ЮMoney - <b>{usr.balance * 0.9} ₽</b>\n🥝 QIWI - <b>{usr.balance * 0.9} ₽</b>\n💳 CARDS- <b>{cards_amt_avaliable} ₽</b>\n\n* Минимальная сумма вывода - <b>500₽</b>",
        parse_mode="HTML",
        reply_markup=keyboard
    )

    return 0

async def ask_payment_sum(update:Update, context:CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    payment_method = update.message.text.split()[1:]
    
    if usr.balance < (500 / 0.9):
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"😐 Минимальная сумма вывода - <b>500₽</b>.\nПо всем вопросам: @i_vovani",
	    parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )

        return ConversationHandler.END

    if len(payment_method) == 0:
        await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"😔 Введено невалидное значение. Попробуйте еще раз.\n\nАдмин: @ivovani",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
        )
        return ConversationHandler.END

    if "qiwi" in payment_method[0].lower().strip():
        if len(payment_method) != 2:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"😔 Введено невалидное значение. Попробуйте еще раз.\n\nАдмин: @ivovani",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )
        
            return ConversationHandler.END
        
        if payment_method[1].lower().strip() in ("карта", "номер", "ник"):
            context.user_data["payment_method"] = " ".join(payment_method)
            context.user_data["comission"] = 10

        else:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"😔 Введено невалидное значение. Попробуйте еще раз.\n\nАдмин: @ivovani",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )
        
            return ConversationHandler.END
        
    elif "юмани" in payment_method[0].lower().strip() or "остальные карты" in f"{' '.join(payment_method).lower()}":
        context.user_data["payment_method"] = " ".join(payment_method)
        context.user_data["comission"] = 10

    else:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"😔 Введено невалидное значение. Попробуйте еще раз.\n\nАдмин: @ivovani",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )

        return ConversationHandler.END
    
    if "остальные карты" in context.user_data["payment_method"].lower().strip():
        sum_avaliable = usr.balance * (1 - context.user_data['comission'] / 100) - 50
    else:
        sum_avaliable = usr.balance * (1 - context.user_data['comission'] / 100)


    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"💸 Введите сумму не более <b>{sum_avaliable} ₽</b>\n🙂 При выводе указывайте сумму не более <b>15.000₽</b> за один раз!\n\n* Минимальная сумма вывода - <b>500₽</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
        ),
    )

    return 1

async def ask_for_credentials(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    amt = update.message.text

    try:
        amt = int(amt.strip())
        if "остальные карты" in context.user_data["payment_method"].lower().strip():
            avaliable_sum = usr.balance * (1 - context.user_data['comission'] / 100) - 50
        else:
            avaliable_sum = usr.balance * (1 - context.user_data['comission'] / 100)

        if amt > avaliable_sum:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"😐 Вы ввели сумму, превышающую доступную.\n🤑 Вам доступно: <b>{avaliable_sum}₽</b>\nПо всем вопросам: @i_vovani",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )

            return ConversationHandler.END

        if amt < 500:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"😐 Минимальная сумма вывода - <b>500₽</b>.\n🤑 Вам доступно: <b>{avaliable_sum}₽</b>\nПо всем вопросам: @i_vovani",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )

            return ConversationHandler.END


        context.user_data["withdraw_amt"] = amt

        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"💰 <b>Введите реквизиты:</b>\n💳 Карту/Счет необходимо ввести <b><i>СЛИТНО!</i></b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )

        return 2

    except:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"😳 Введено невалидное значение суммы.\n\nПо всем вопросам: @i_vovani",
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )

        return ConversationHandler.END

async def ask_for_acception_transaction(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    credentials = update.message.text
    
    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"<b>⚡️ Подтвердите выплату</b>\n💳 Реквизиты: <b>{credentials}</b>\n💰 Сумма: <b>{context.user_data['withdraw_amt']}₽</b>\n🔐 Способ оплаты: <b>{context.user_data['payment_method']}</b>\n🧮 Комиссия: <b>{context.user_data['comission']}%</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton(text="Подтверждаю ✅")],
            [KeyboardButton(text="Отклоняю 📛")]
        ], one_time_keyboard=True, resize_keyboard=True)
    )

    return 3

async def deny_usr_transaction(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    msg = message.text.split("\n")
    tg_id, payment_id = msg[1].split(":")[1].strip(), msg[-1].split(":")[1].strip()

    if usr.is_superuser:
        
        if CustomUser.objects.filter(telegram_id_in_admin_bot=tg_id).exists():
            payeer = CustomUser.objects.filter(telegram_id_in_admin_bot=tg_id).first()
            payment = AdminTransaction.objects.filter(payment_id=payment_id).first()

            payment.status = "Отменен"
            payment.save()

            await context.bot.send_message(
                payeer.telegram_id_in_admin_bot,
                f"<b>Заявка на вывод отменена ❌</b>\n\nПричина: <b>неверные реквизиты</b>\n\nОбратитесь к @i_vovani",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )

            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                "Ответ пользователю доставлен.",
            )

        else:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"К сожалению, пользователя с id={tg_id} не существует. \n\nЕсли произошла ошибка, обратитесь к @i_vovani"
            )

    else:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"🙀 К сожалению, у вас недостаточно прав. Для совершения этой операции необходимы права администратора.\n\n Если произошла ошибка, обратитесь к @i_vovani",
            parse_mode="HTML",  
        )

async def finish_usr_transaction(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    msg = message.text.split("\n")
    tg_id, payment_id, amt = msg[1].split(":")[1].strip(), msg[-1].split(":")[1].strip(), int(msg[-2].split(":")[1][:-1])

    if usr.is_superuser:
        
        if CustomUser.objects.filter(telegram_id_in_admin_bot=tg_id).exists():
            payeer = CustomUser.objects.filter(telegram_id_in_admin_bot=tg_id).first()
            payment = AdminTransaction.objects.filter(payment_id=payment_id).first()

            payment.status = "Проведен"
            payment.income = amt * (payment.comission / 100)
            payeer.balance -= amt

            payeer.save()
            payment.save()

            await context.bot.send_message(
                payeer.telegram_id_in_admin_bot,
                f"<b>Заявка на вывод выполнена ✅</b>\n\nНомер заявки: <b>{payment_id}</b>\n\nЕсли произошла ошибка, обратитесь к @i_vovani",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup.from_button(
                    InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
                ),
            )

            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                "Ответ пользователю доставлен.",
            )

        else:
            await context.bot.send_message(
                usr.telegram_id_in_admin_bot,
                f"К сожалению, пользователя с id={tg_id} не существует. \n\nЕсли произошла ошибка, обратитесь к @i_vovani"
            )

    else:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"🙀 К сожалению, у вас недостаточно прав. Для совершения этой операции необходимы права администратора.\n\n Если произошла ошибка, обратитесь к @i_vovani",
            parse_mode="HTML",  
        )

async def usr_acception_transaction(update:Update, context:CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    choice = update.message.text.strip().lower()
    payment_id = str(uuid.uuid4())

    transaction = AdminTransaction(
            payment_id=payment_id,
            withdraw_type=context.user_data["payment_method"],
            payment_sum=context.user_data["withdraw_amt"],
            comission=context.user_data["comission"],
            payeer=usr   
    )

    if "подтверждаю" in choice:
        transaction.status = "В работе"
        admin = CustomUser.objects.filter(username="i_vovani").first()
        
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"✅ Ваша заявка на вывод одобрена!\nКогда она будет исполнена, вы получите уведомление в этом чате.\n\nID заявки - <b>{payment_id}</b> \n\nПо всем вопросам: @i_vovani",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )

        await context.bot.send_message(
            admin.telegram_id_in_admin_bot,
            f"🍅 Новая заявка на выплату:\nTG ID: <b>{usr.telegram_id_in_admin_bot}</b>\nПользователь: <b>@{usr.username}</b>\nТип вывода: <b>{context.user_data['payment_method']}</b>\nСумма: <b>{context.user_data['withdraw_amt']}₽</b>\nID заявки: <b>{payment_id}</b>",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text="Выполнена ✅", callback_data="accept_transaction"),
                    InlineKeyboardButton(text="Отменена ⛔️", callback_data="deny_transaction"),
                ]
            ])
        )
        transaction.save()

        return ConversationHandler.END

    if "отклоняю" in choice:
        transaction.status = "Отменен"
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"👁 Данные обновлены!",
            parse_mode="HTML",
            reply_markup=VERIFIED_MARKUP
        )

        transaction.save()  
        return ConversationHandler.END
    

    await context.bot.send_message(
        usr.telegram_id_in_admin_bot,
        f"😳 Получено некорректное значение.\n\nПо всем вопросам: @i_vovani",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
        ),
    )

async def transaction_list(update:Update, context:CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    transactions = AdminTransaction.objects.filter(payeer=usr).all()[:5]
    end_msg = "<b>📝 Ваши 5 последних транзакций:</b>\n\n"

    if len(transactions) == 0:
        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            f"😔 У вас пока нет ни одной транзакции...",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )

    else:
        for transaction in transactions:
            end_msg += f"ID: <b>{transaction.payment_id}</b>\nТип вывода: <b>{transaction.withdraw_type}</b>\nСумма: <b>{transaction.payment_sum}₽</b>\nСтатус: <b>{transaction.status}</b>\n\n"

        await context.bot.send_message(
            usr.telegram_id_in_admin_bot,
            end_msg,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup.from_button(
                InlineKeyboardButton(text="Вернуться в меню 📦", callback_data="main_menu"),
            ),
        )


def main() -> None:
    """Run the bot."""

    application = Application.builder().token(os.environ.get("ADMIN_BOT_TOKEN")).build()
    
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(CallbackQueryHandler(start, "main_menu"))

    application.add_handler(CallbackQueryHandler(user_bots_info, "bots_management"))
    application.add_handler(CallbackQueryHandler(stat, "stat"))

    application.add_handler(CallbackQueryHandler(transaction_list, "withdraw_list"))

    create_payment_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_payment_method, "create_withdraw")],
        states={
            0: [MessageHandler(filters.TEXT, ask_payment_sum)],
            1: [MessageHandler(filters.TEXT, ask_for_credentials)],
            2: [MessageHandler(filters.TEXT, ask_for_acception_transaction)],
            3: [MessageHandler(filters.TEXT, usr_acception_transaction)]
        },
        fallbacks=[]
    )
    application.add_handler(create_payment_conv_handler)

    application.add_handler(CallbackQueryHandler(finish_usr_transaction, "accept_transaction"))
    application.add_handler(CallbackQueryHandler(deny_usr_transaction, "deny_transaction"))

    verify_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(verification, "verify")],
        states={
            0: [MessageHandler(filters.TEXT, complete_verification)],
            
        },
        fallbacks=[],
    )
    application.add_handler(verify_conv_handler)

    application.add_handler(CallbackQueryHandler(accept_user, "accept_usr"))
    application.add_handler(CallbackQueryHandler(deny_user, "deny_usr"))

    create_bot_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_bot_name, "create_bot_for_admin")],
        states={
            0: [MessageHandler(filters.TEXT, ask_for_bot_token)],
            1: [MessageHandler(filters.TEXT, create_bot_by_usr_token)]
        },
        fallbacks=[]
    )
    application.add_handler(create_bot_conv_handler)

    application.add_handler(CallbackQueryHandler(stop_activate_bot))
    application.add_handler(MessageHandler("Меню 📥", start))

    application.run_polling()


class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):        
        main()

        
        
        
