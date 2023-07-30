from main.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, re
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

async def start(update: Update, context: CallbackContext):
    """
        Обработчик команды /start
    """
    usr, _, _ = await user_get_by_update(update)

    if usr.verified_usr:
        active_table_id = context.user_data.get("active_table_id", "")

        if active_table_id in [tbl.id for tbl in usr.get_tables()]:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать новую таблицу ➕",
                    callback_data="create_table",
                )],
                [InlineKeyboardButton(
                    text="Добавить запись 💸",
                    callback_data="add_operation",
                )],
                [InlineKeyboardButton(
                    text="Выбор активной таблицы 📃",
                    callback_data="list_table",
                )],
                [InlineKeyboardButton(
                    text="Сводка по таблицам 📊",
                    callback_data="table_analytics",
                )],
                [InlineKeyboardButton(
                    text="История операций 🔭",
                    callback_data="operation_history",
                )]
            ])

            active_table = Table.objects.get(pk=active_table_id)

            await context.bot.send_video(
                usr.telegram_chat_id,
                "https://media2.giphy.com/media/67ThRZlYBvibtdF9JH/giphy.gif?cid=ecf05e47u0hkmcznkfg7hju8bo77hffom4asrl76jmv4xlpd&ep=v1_gifs_search&rid=giphy.gif&ct=g",
                caption=f"😽 С возвращением, <b>{usr.username}</b>\n💰 Уже подсчитываю ваши миллионы\n\n<u><i>Ваша активная таблица</i></u>:\n\n🔗 Название: <b>{active_table.name}</b>\n⚰️ id: <b>{active_table.id}</b>",
                parse_mode="HTML",
                width=150,
                height=150,
                reply_markup=markup
            )
        else:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать новую таблицу ➕",
                    callback_data="create_table",
                )],
                [InlineKeyboardButton(
                    text="Выбор активной таблицы 📃",
                    callback_data="list_table",
                )],
                [InlineKeyboardButton(
                    text="Сводка по таблицам 📊",
                    callback_data="table_analytics",
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
                        callback_data="menu"
                    )]
                ])
            )

            return None

        new_table = Table(
            name=update.message.text
        )
        new_table.save()
        usr.tables.add(new_table)

        context.user_data["active_table_id"] = new_table.id

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"✅ Таблица <b>{new_table.name.capitalize()}</b> успешно создана и выбрана в качестве активной.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Добавить запись 🏧",
                    callback_data="add_operation"
                )],
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
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
                    callback_data="menu"
                )]
            ])
        )

    return ConversationHandler.END

async def list_table(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    
    user_tables = usr.get_tables()

    if len(user_tables) != 0:
        msg = ""
        reply_keyboard = []
        for table in user_tables:
            msg += f"<b>ID</b> - {table.id}{' ' * (4 - len(str(table.id)))} <b>{table.name}{' ' * (12 - len(table.name))}</b>\n"
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
                        callback_data="menu"
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
                    callback_data="menu"
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
                    callback_data="menu"
                )]
            ])
        )

    return ConversationHandler.END

async def ask_for_operation_type(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    
    if Table.objects.filter(id=context.user_data.get("active_table_id",'')).exists():
        if Table.objects.get(pk=context.user_data.get("active_table_id",'')) in usr.get_tables():
                        
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"☑️ Выберите тип операции.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Доход ➕",
                        callback_data="income"
                    )],
                    [InlineKeyboardButton(
                        text="Расход ➖",
                        callback_data="consumption"
                    )],
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    )]
                ])
            )

            return 0
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"❌ Вы не являетесь владельцем таблицы с id = {context.user_data.get('active_table_id','')}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    )]
                ])
            )

    else:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"❌ Вы не выбрали активную таблицу. Сделайте это в списке таблиц.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
        )

    return ConversationHandler.END

async def add_income_operation(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    await context.bot.send_message(
            usr.telegram_chat_id,
            f"Вы выбрали тип - <b>Доход</b>\n\nТеперь напишите мне сумму платежа.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
    )

    context.user_data["payment_type"] = "Доход"

    return 1

async def add_consumption_operation(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    await context.bot.send_message(
            usr.telegram_chat_id,
            f"Вы выбрали тип - <b>Расход</b>\n\nТеперь напишите мне сумму платежа.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
    )

    context.user_data["payment_type"] = "Расход"

    return 1

async def get_operation_amount(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    try:
        context.user_data["payment_amount"] = int(update.message.text.strip())
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🥶 Отлично, фиксируем сумму = <b>{int(update.message.text.strip())}₽</b> \n\nТеперь пришли мне описание платежа и закончим на этом.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
        )

        return 2
    
    except Exception as e:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"❌ Введено некорректное значение суммы.\n\n<b>Ошибка:</b><i>{e}</i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
        )

    return ConversationHandler.END

async def create_operation(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    desc = update.message.text.strip().capitalize()
    table_id = context.user_data.get("active_table_id",'')
    if Table.objects.filter(id=table_id).exists():
        if Table.objects.get(pk=table_id) in usr.get_tables():
            try:
                if context.user_data["payment_type"] == "Доход":
                    new_operation = Operation(
                        type="Доход",
                        amount=context.user_data["payment_amount"],
                        description=desc,
                        creator=usr,
                        table=Table.objects.get(pk=table_id)
                    )

                    new_operation.save()

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"✅ Операция с типом <b>Доход</b> успешно добавлена.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="В меню 🍺",
                                callback_data="menu"
                            )]
                        ])
                    )

                    return ConversationHandler.END


                elif context.user_data["payment_type"] == "Расход":
                    new_operation = Operation(
                        type="Расход",
                        amount=context.user_data["payment_amount"],
                        description=desc,
                        creator=usr,
                        table=Table.objects.get(pk=table_id)
                    )

                    new_operation.save()

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"✅ Операция с типом <b>Расход</b> успешно добавлена.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="В меню 🍺",
                                callback_data="menu"
                            )]
                        ])
                    )

                    return ConversationHandler.END

                else:
                    raise Exception("Ошибка внутреннего хранилища. Попробуйте перезапустить бота")
                
            except Exception as e:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"❌ Не удалось добавить операцию.\n\n<b>Ошибка:</b><i>{e}</i>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 🍺",
                            callback_data="menu"
                        )]
                    ])
                )

                return ConversationHandler.END

        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"❌ Вы не являетесь владельцем таблицы с id = {context.user_data.get('active_table_id','')}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    )]
                ])
            )

            return ConversationHandler.END

    else:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"❌ Вы не выбрали активную таблицу. Сделайте это в списке таблиц.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
        )

        return ConversationHandler.END

async def table_analytics(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    end_msg = "📊 <u><b>Сводка</b></u>\n\n"

    total_income, total_consumption = 0, 0 

    for table in usr.get_tables():
        operations = Operation.objects.filter(table=table).all()
        table_income, table_consumption = 0, 0

        if len(operations) != 0:
            for operation in operations:
                if operation.type == "Доход":
                    table_income += operation.amount
                else:
                    table_consumption += operation.amount

            end_msg += f"🔗 Таблица <b>{table.name}</b>:\n🤑 Доход: <b>{table_income}₽</b>\n😢 Расход: <b>{table_consumption}₽</b>\n💸 <b>Прибыль</b>: <b>{table_income - table_consumption}₽</b>\n\n"
        else:
            end_msg += f"🔗 Таблица <b>{table.name}</b>:\n🤑 Доход: <b>{table_income}₽</b>\n😢 Расход: <b>{table_consumption}₽</b>\n💸 <b>Прибыль</b>: <b>{table_income - table_consumption}₽</b>\n\n"
        
        total_income += table_income
        total_consumption += table_consumption

    end_msg += f"\n🍪 <u><b>Общая ситуация</b></u>\n\n🔎 Общий доход: <b>{total_income}₽</b>\n😔 Общий расход: <b>{total_consumption}₽</b>\n💩 <b>Общая прибыль</b>: <b>{total_income - total_consumption}₽</b>"

    await context.bot.send_message(
        usr.telegram_chat_id,
        end_msg,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="В меню 🍺",
                callback_data="menu"
            )]
        ])
    )

async def ask_for_history_type(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    await context.bot.send_message(
        usr.telegram_chat_id,
        f"🔩 <b>{usr.username}</b>, введите диапазон дат для среза операций.\n\nФормат данных <b>dd-mm-yy</b> <b>dd-mm-yy</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="В меню 🍺",
                callback_data="menu"
            )]
        ])
    )

    return 0

async def show_history(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)
    table_id = context.user_data.get("active_table_id",'')

    message = list(filter(lambda x: x != " ", update.message.text.lower().strip().split()))
    expression = re.compile("(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-(19|20)\d\d")

    if len(message) == 2:
        if expression.match(message[0]) and expression.match(message[0]):
            date_start, date_end = "-".join(reversed(message[0].split("-"))), "-".join(list(reversed(message[1].split("-")[1:])) + [str(int(message[1].split("-")[0]) + 1)])
            
            if Table.objects.filter(id=table_id).exists():
                if Table.objects.get(pk=table_id) in usr.get_tables():
                    users_table = Table.objects.get(pk=table_id)
                    
                    try:
                        end_msg = f"⏳<b><u>История</u></b>\n\n<b>🧩 Таблица:</b> <i>{users_table.name}</i>\n\n<b>🕐 Дата начала:</b> {date_start}\n<b>🕤 Дата конца:</b> {date_end}\n\n"
                        active_table_operations = Operation.objects.filter(
                            date__range=[date_start, date_end],
                            table=users_table
                        ).all().order_by('-date')
                        
                        total_slice_income, total_slice_consumption = 0, 0
                        for table in usr.get_tables():
                            table_operations = Operation.objects.filter(
                                date__range=[date_start, date_end],
                                table=table
                            ).all().order_by('-date')
                            
                            for operation in table_operations:
                                if operation.type.lower() == "доход":
                                    total_slice_income += operation.amount
                                elif operation.type.lower() == "расход":
                                    total_slice_consumption += operation.amount


                        if len(active_table_operations) != 0:
                            active_table_slice_income, active_table_slice_consumption = 0, 0 
                            
                            income_msg = f"💸 <b><u>Доходы:</u></b>\n\n"
                            consumption_msg = f"🤬 <b><u>Расходы:</u></b>\n\n"

                            for operation in active_table_operations:
                                 
                                if operation.type.lower() == "доход":
                                    active_table_slice_income += operation.amount
                                    income_msg += f"<i>{str(operation.date).split()[0]}</i> - <b>{operation.amount}₽</b> - <b>{operation.description}</b>\n"
                                
                                elif operation.type.lower() == "расход":
                                    active_table_slice_consumption += operation.amount
                                    consumption_msg += f"<i>{str(operation.date).split()[0]}</i> - <b>{operation.amount}₽</b> - <b>{operation.description}</b>\n"
                                
                            end_msg = end_msg + income_msg + "\n" + consumption_msg

                            end_msg += f"\n\n🗿<b><u>Сводка по активной таблице:</u></b>\n\n🔎 Общий доход: <b>{active_table_slice_income}₽</b>\n😔 Общий расход: <b>{active_table_slice_consumption}₽</b>\n💩 <b>Общая прибыль</b>: <b>{active_table_slice_income - active_table_slice_consumption}₽</b>\n\n"
                            end_msg += f"\n🍺<b><u>Сводка по всем таблицам:</u></b>\n\n🔎 Общий доход: <b>{total_slice_income}₽</b>\n😔 Общий расход: <b>{total_slice_consumption}₽</b>\n💩 <b>Общая прибыль</b>: <b>{total_slice_income - total_slice_consumption}₽</b>"
                            
                        else:
                            end_msg = f"⏳<b><u>История</u></b>\n\n<b>🧩 Таблица:</b> <i>{users_table.name}</i>\n\n<b>🕐 Дата начала:</b> {date_start}\n<b>🕤 Дата конца:</b> {date_end}\n\n😵‍💫 Ни одной записи по вашему запросу не найдено."
                        
                        await context.bot.send_message(
                            usr.telegram_chat_id,
                            end_msg,
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton(
                                    text="Еще раз 🚀",
                                    callback_data="operation_history"
                                )],
                                [InlineKeyboardButton(
                                    text="В меню 🍺",
                                    callback_data="menu"
                                )]
                            ])
                        )

                    except Exception as e:
                        await context.bot.send_message(
                            usr.telegram_chat_id,
                            f"❌ Произошла ошибка во время поиска таблицы.\n\n<b>Ошибка:</b><i>{e}</i>",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton(
                                    text="В меню 🍺",
                                    callback_data="menu"
                                )]
                            ])
                        )
                else:
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"❌ Вы не являетесь владельцем таблицы с id = {context.user_data.get('active_table_id','')}",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="В меню 🍺",
                                callback_data="menu"
                            )]
                        ])
                    )

            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"❌ Вы не выбрали активную таблицу. Сделайте это в списке таблиц.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 🍺",
                            callback_data="menu"
                        )]
                    ])
                )

        else:
            await context.bot.send_message(
            usr.telegram_chat_id,
            f"👿 Получено некорректное значение дат, выйдите в меню и попробуйте еще раз.\n\n<i>Будьте внимательны, формат даты: <b>dd-mm-yy dd-mm-yy</b></i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
        )
            
    else:
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"👿 Получено некорректное значение дат, выйдите в меню и попробуйте еще раз.\n\n<i>Будьте внимательны, формат даты: <b>dd-mm-yy dd-mm-yy</b></i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            ])
        )

    return ConversationHandler.END


async def garbage_callback(update: Update, context: CallbackContext):
    usr, _, _ = await user_get_by_update(update)

    await context.bot.send_message(
        usr.telegram_chat_id,
        f"Мы такое не обрабатываем. Во всем виновата Америка <b>Z</b> <b>V</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="В меню 🍺",
                callback_data="menu"
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
    application.add_handler(CallbackQueryHandler(table_analytics, "table_analytics"))

    add_operation_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_operation_type, "add_operation")],
        states={
            0: [CallbackQueryHandler(add_income_operation, "income"), CallbackQueryHandler(add_consumption_operation, "consumption")],
            1: [MessageHandler(filters.TEXT, get_operation_amount)],
            2: [MessageHandler(filters.TEXT, create_operation)]

        },
        fallbacks=[CallbackQueryHandler(start, "menu")]
    )
    application.add_handler(add_operation_conv_handler)

    create_table_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_table_name, "create_table")],
        states={
            0: [MessageHandler(filters.TEXT, create_table)],
        },
        fallbacks=[CallbackQueryHandler(start, "menu")]
    )
    application.add_handler(create_table_conv_handler)

    choose_table_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(list_table, "list_table")],
        states={
            0: [MessageHandler(filters.TEXT, choose_table)],
        },
        fallbacks=[CallbackQueryHandler(start, "menu")]
    )
    application.add_handler(choose_table_conv_handler)
 
    get_history_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_for_history_type, "operation_history")],
        states={
            0: [MessageHandler(filters.TEXT, show_history)]
        },
        fallbacks=[CallbackQueryHandler(start, "menu")]
    )
    application.add_handler(get_history_conv_handler)

    application.add_handler(CallbackQueryHandler(start, "menu"))
    application.add_handler(MessageHandler(filters.TEXT, garbage_callback))
 
    application.run_polling()


class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):        
        main()

        
        
        
