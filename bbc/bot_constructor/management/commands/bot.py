from bot_constructor.models import *

from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, requests, json, uuid
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

HOST = "172.16.238.10"
BOTS_LIMIT = 1

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

    if not AdminApplication.objects.filter(user=usr).exists():
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
            new_usr = CustomUser.objects.filter(telegram_id_in_admin_bot=new_user_id)
            
            application = AdminApplication.objects.filter(
                user=new_usr[0]
            )
            application.update(
                status="Denied"
            )

            await context.bot.delete_message(
                usr.telegram_id_in_admin_bot,
                update.effective_message.id
            )
            
            await context.bot.send_message(
                new_usr[0].telegram_id_in_admin_bot,
                f"✖ К сожалению, ваша заявка <b>{application.application_number}</b> была отклонена\nПопробуйте еще раз, либо обратитесь к администратору\n\nАдминистратор: @i_vovani ",
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
                status="Accepted"
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
    
    if len(Bot.objects.filter(owner=usr).all()) == BOTS_LIMIT:
        context.bot.send_message(
            usr.telegram_id_in_admin_bot, 
            f"<b>{usr.usrname}</b>, вы превысили лимит на создание ботов.",
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

    if Bot.objects.filter(bot_token=message.text.strip()).exists():
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

    r = requests.post(f'http://{HOST}:8000/api/constructor/create_bot', headers=headers, data=data)

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


    if len(user_bots) < BOTS_LIMIT:
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
            
            r = requests.post(f'http://{HOST}:8000/api/constructor/start_bot', headers=headers, data=data)

            if r.status_code == 200:
                bot_by_id.is_active = True
                bot_by_id.save()

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

            r = requests.post(f'http://{HOST}:8000/api/constructor/stop_bot', headers=headers, data=data)

            print(r.json())

            if r.status_code == 200:
                bot_by_id.is_active = False
                bot_by_id.save()

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
    end_message = f"💰 Актуальный баланс: <b>{usr.balance}₽</b>\n\n📊 Суммарный оборот: <b>{usr.total_income}₽</b>"

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

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(os.environ.get("ADMIN_BOT_TOKEN")).build()
    
    application.add_handler(CommandHandler("start", start)) 
    application.add_handler(CallbackQueryHandler(start, "main_menu"))

    application.add_handler(CallbackQueryHandler(accept_user, "accept_usr"))
    application.add_handler(CallbackQueryHandler(deny_user, "deny_usr"))

    application.add_handler(CallbackQueryHandler(user_bots_info, "bots_management"))
    application.add_handler(CallbackQueryHandler(stat, "stat"))

    create_bot_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_bot_name, "create_bot_for_admin")],
        states={
            0: [MessageHandler(filters.TEXT, ask_for_bot_token)],
            1: [MessageHandler(filters.TEXT, create_bot_by_usr_token)]
        },
        fallbacks=[]
    )
    application.add_handler(create_bot_conv_handler)

    verify_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(verification, "verify")],
        states={
            0: [MessageHandler(filters.TEXT, complete_verification)],
            
        },
        fallbacks=[],
    )
    application.add_handler(verify_conv_handler)


    application.add_handler(CallbackQueryHandler(stop_activate_bot))
    application.run_polling()


class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):        
        main()

        
        
        