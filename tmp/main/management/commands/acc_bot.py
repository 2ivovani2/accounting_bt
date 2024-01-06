from main.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, re, random, io
from datetime import datetime, timedelta
warnings.filterwarnings("ignore")

import numpy as np, matplotlib.pyplot as plt
from PIL import Image

from django.core.management.base import BaseCommand

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
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

        usr, _ = CustomUser.objects.update_or_create(
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
    
class Bot:
    """
        Класс, инициализирующий instance бота
    """

    def __init__(self) -> None:
        self.application = Application.builder().token(os.environ.get("ACCOUNT_BOT_TOKEN")).build()

    @check_user_status
    async def _start(update: Update, context: CallbackContext):
        """
            Обработчик команды /start

        """

        usr, _, _ = await user_get_by_update(update)
        active_table_id = context.user_data.get("active_table_id", "")

        pictures_for_menu = [
            "https://media2.giphy.com/media/67ThRZlYBvibtdF9JH/giphy.gif?cid=ecf05e47u0hkmcznkfg7hju8bo77hffom4asrl76jmv4xlpd&ep=v1_gifs_search&rid=giphy.gif&ct=g",
            "https://media.giphy.com/media/JtBZm3Getg3dqxK0zP/giphy-downsized-large.gif",
            "https://media.giphy.com/media/xTiTnqUxyWbsAXq7Ju/giphy.gif",
            "https://media.giphy.com/media/YRw676NBrmPeM/giphy.gif",
            "https://media.giphy.com/media/3oEdvbpl0X32bXD2Vi/giphy.gif",
            "https://media.giphy.com/media/XGP7mf38Vggik/giphy.gif",
            "https://media.giphy.com/media/x33Pp717M1gc0/giphy.gif"
                
        ]

        if active_table_id in [tbl.id for tbl in usr.get_tables()]:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать таблицу ➕",
                    callback_data="create_table",
                )],
                [InlineKeyboardButton(
                    text="Выбор таблицы 📃",
                    callback_data="list_table",
                )],
                [InlineKeyboardButton(
                    text="Добавить запись 💸",
                    callback_data="add_operation",
                )],
                [InlineKeyboardButton(
                    text="Категории 🐋",
                    callback_data="category_work",
                ),
                ],
                [InlineKeyboardButton(
                    text="Сводка 📊",
                    callback_data="table_analytics",
                ),
                InlineKeyboardButton(
                    text="История 📟",
                    callback_data="operation_history",
                )
                ],
                [InlineKeyboardButton(
                    text="White Paper 📝",
                    url="https://teletype.in/@ivovani/acc_bot_manual"
                ),
                InlineKeyboardButton(
                    text="Поддержка 🌻",
                    url="https://t.me/i_vovani"
                )],

                [InlineKeyboardButton(text="Админка 👀", web_app=WebAppInfo(url=f"{os.environ.get('DOMAIN_NAME')}/admin"))] if usr.is_superuser else [],
                
            ])

            active_table = Table.objects.get(pk=active_table_id)
            income_cats, consumption_cats = "\n".join(["🔹 " + cat.name for cat in Category.objects.filter(table=active_table, type="Доход").all()]), "\n".join(["🔸 " + cat.name for cat in Category.objects.filter(table=active_table, type="Расход")])
            
            if income_cats != "" and consumption_cats != "":
                cats_msg = f"<i><u>Доходные категории</u></i>:\n\n{income_cats}\n\n<i><u>Расходные категории</u></i>:\n\n{consumption_cats}"
            elif income_cats == "" and consumption_cats != "":
                cats_msg = f"<i><u>Доходные категории</u></i>:\n\n😵 У вас пока нет ни одной доходной категории.\n\n<i><u>Расходные категории</u></i>:\n\n{consumption_cats}"
            elif income_cats != "" and consumption_cats == "":
                cats_msg = f"<i><u>Доходные категории</u></i>:\n\n{income_cats}\n\n<i><u>Расходные категории</u></i>:\n\n😵 У вас пока нет ни одной расходной категории."
            else:
                cats_msg = f"<i><u>Доходные категории</u></i>:\n\n😵 У вас пока нет ни одной доходной категории.\n\n<i><u>Расходные категории</u></i>:\n\n😵 У вас пока нет ни одной расходной категории."
                    


            await context.bot.send_video(
                usr.telegram_chat_id,
                random.choice(pictures_for_menu),
                caption=f"😽 С возвращением, <b>{usr.username}</b>\n💰 Уже подсчитываю ваши миллионы\n\n<u><i>Ваша активная таблица</i></u>:\n\n🔗 Название: <b>{active_table.name}</b>\n⚰️ id: <b>{active_table.id}</b>\n\n{cats_msg}",
                parse_mode="HTML",
                width=150,
                height=150,
                reply_markup=markup
            )
        else:
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать таблицу ➕",
                    callback_data="create_table",
                )],
                [InlineKeyboardButton(
                    text="Выбор таблицы 📃",
                    callback_data="list_table",
                )],
                [InlineKeyboardButton(
                    text="Сводка 📊",
                    callback_data="table_analytics",
                )],
                [InlineKeyboardButton(
                    text="White Paper 📝",
                    url="https://teletype.in/@ivovani/acc_bot_manual"
                ),
                InlineKeyboardButton(
                    text="Поддержка 🌻",
                    url="https://t.me/i_vovani"
                )],
                [InlineKeyboardButton(text="Админка 👀", web_app=WebAppInfo(url=f"{os.environ.get('DOMAIN_NAME')}/admin"))] if usr.is_superuser else []
            ])

            await context.bot.send_video(
                usr.telegram_chat_id,
                random.choice(pictures_for_menu),
                caption=f"😽 С возвращением, <b>{usr.username}</b>\n💰 Уже подсчитываю ваши миллионы.\n\n⚠️ Чтобы получить доступ к операциям, выберите активную таблицу.",
                parse_mode="HTML",
                width=150,
                height=150,
                reply_markup=markup
            )
        
        return ConversationHandler.END

    @check_user_status
    async def _table_analytics(update: Update, context: CallbackContext):
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

    @check_user_status
    async def _start_category_menu(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)

        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="Добавить категорию 🧤",
                callback_data="add_category",
            )], 
            [InlineKeyboardButton(
                text="Изменить категорию 🎄",
                callback_data="change_category",
            )],
            [InlineKeyboardButton(
                text="Удалить категорию 🤡",
                callback_data="delete_category",
            )],
            [InlineKeyboardButton(
                text="В меню 🍺",
                callback_data="menu"
            ),]
        ])

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"😳 <b>{usr.username}</b>, Выберите, что вы хотите сделать с категориями",
            parse_mode="HTML",
            reply_markup=markup
        )

    @check_user_status
    async def _analyse_history(update: Update, context: CallbackContext):
        """
            Аналитика истории, в качестве категорий
        """
        usr, _, _ = await user_get_by_update(update)
        table_id = context.user_data.get("active_table_id",'')
        
        if Table.objects.filter(id=table_id).exists():
            if Table.objects.get(pk=table_id) in usr.get_tables():
                active_table = Table.objects.get(pk=table_id)
                try:
                    date_start, date_end = context.user_data.get("date_start", ""), context.user_data.get("date_end", ""), 
                    active_table_operations = Operation.objects.filter(
                        date__range=[date_start, date_end],
                        table=active_table, 
                    ).all().order_by('-date')

                    cat_data_dict = {
                        "Без категории":[]
                    }

                    for operation in active_table_operations:
                        if operation.category:
                            if operation.category.name not in cat_data_dict.keys():
                                cat_data_dict[operation.category.name] = [
                                    operation
                                ]
                            else:
                                cat_data_dict[operation.category.name].append(operation)
                        else:
                            cat_data_dict["Без категории"].append(operation)

                    end_msg = f"🦉 <b><u>Анализ категорий</u></b>\n\n<b>🧩 Таблица:</b> <i>{active_table.name}</i>\n\n<b>🕐 Дата начала:</b> {date_start}\n<b>🕤 Дата конца:</b> {date_end}\n\n"
                    
                    if len(cat_data_dict["Без категории"]) == 0:
                        del cat_data_dict["Без категории"]

                    for category in cat_data_dict.keys():
                        amounts = []
                        if category != "Без категории":
                            category_type = Category.objects.filter(name=category).first().type
                        else:
                            category_type = "Без тип"    

                        for operation in cat_data_dict[category]:
                            amounts.append(operation.amount)
                            
                        end_msg += f"🔸 <b><u>Категория</u></b>: <i>{category}</i>\n\n∙ Тип категории: <b>{category_type}ная</b>\n∙ Общий объем денег: <b>{sum(amounts)}₽</b>\n∙ Средний объем денег: <b>{sum(amounts) / len(amounts) if len(amounts) != 0 else 0:.2f}₽</b>\n\n"
                        
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        end_msg,
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="В меню 🍺",
                                callback_data="menu"
                            ),
                            InlineKeyboardButton(
                                text="Еще раз 🚀",
                                callback_data="operation_history"
                            )]
                        ])
                    )
                
                except Exception as e:
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"❌ Произошла ошибка во время формирования аналитики.\n\n<b>Ошибка:</b><i>{e}</i>",
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

    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """
        self.application.add_handler(CommandHandler("start", self._start))
        
        self.application.add_handler(CallbackQueryHandler(self._table_analytics, "table_analytics"))
        self.application.add_handler(CallbackQueryHandler(self._start_category_menu, "category_work"))
        self.application.add_handler(CallbackQueryHandler(self._analyse_history, "analyse_history"))

        return self.application

class TableWork(Bot):
    """
        Класс, инициализирующий instance класса для рвботы с таблицами
    """

    def __init__(self, application) -> None:
        self.application = application 

    @check_user_status
    async def _ask_for_table_name(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)

        if usr.can_create_tables:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🖍 Напишите название для вашей новой таблицы.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Отменить ⛔️",
                        callback_data="menu"
                    )]
                ])
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

    @check_user_status
    async def _create_table(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)

        try:
            if len(update.message.text) > 255:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"👿 Допустимное количесвто символов превышено.\n\nМаксимум - <b>255</b>\nУ вас - <b>{len(update.message.text)}</b>",
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
                f"✅ Таблица <b>{new_table.name}</b> успешно создана и выбрана в качестве активной.",
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

    @check_user_status
    async def _list_table(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        
        user_tables = usr.get_tables()

        if len(user_tables) != 0:
            msg = ""
            reply_keyboard = []
            for index in range(0, len(user_tables), 2):
                try:
                    t1, t2 = user_tables[index : index + 2]
                    reply_keyboard.append([InlineKeyboardButton(text=f"{t1.name}", callback_data=f"choose_table_{t1.id}"), InlineKeyboardButton(text=f"{t2.name}", callback_data=f"choose_table_{t2.id}")])
                
                except ValueError:
                    t1 = user_tables[index : index + 2][0]
                    reply_keyboard.append([InlineKeyboardButton(text=f"{t1.name}", callback_data=f"choose_table_{t1.id}"),])

            reply_keyboard.append(
                [InlineKeyboardButton(
                    text="В меню 🍺",
                    callback_data="menu"
                )]
            )

            await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"👺 <b>{usr.username}</b>, выберите таблицу, которую хотите сделать активной из списка ниже:\n\n{msg}",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(reply_keyboard),
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

    @check_user_status
    async def _choose_table(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        
        try:
            id = int(update.callback_query.data.strip().lower().split("_")[-1])
            if id in [tbl.id for tbl in usr.get_tables()]:
                context.user_data["active_table_id"] = id

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🤖 Вы выбрали таблицу <b>{Table.objects.get(pk=id).name}</b>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Добавить запись 💸",
                            callback_data="add_operation",
                        )],
                        [InlineKeyboardButton(
                            text="Категории 🐋",
                            callback_data="category_work",
                        )],
                        [InlineKeyboardButton(
                            text="В меню 🍺",
                            callback_data="menu"
                        ), 
                        InlineKeyboardButton(
                            text="История 📟",
                            callback_data="operation_history",
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

    def register_handlers(self) -> None: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """

        # хэндлер для выбора активной таблицы
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._list_table, "list_table")],
            states={
                0: [CallbackQueryHandler(self._choose_table, "^choose_table_")],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

        # хэндлер для создания новой таблицы
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_table_name, "create_table")],
            states={
                0: [MessageHandler(filters.TEXT, self._create_table)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

class OperationWork(Bot):
    """
        Класс, инициализирующий instance класса для рвботы с операциями
    """

    def __init__(self, application) -> None:
        self.application = application 

    @check_user_status
    async def _ask_for_operation_type(update: Update, context: CallbackContext):
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
                            callback_data="operation_income"
                        )],
                        [InlineKeyboardButton(
                            text="Расход ➖",
                            callback_data="operation_consumption"
                        )],
                        [InlineKeyboardButton(
                            text="Отмена ⛔️",
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

    @check_user_status
    async def _add_operation(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        oper_type = update.callback_query.data.strip().lower().split("_")[-1]
        if oper_type == "income":
            await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"Вы выбрали тип - <b>Доход</b>\n\nТеперь напишите мне сумму платежа.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Отмена ⛔️",
                            callback_data="menu"
                        )]
                    ])
            )

            context.user_data["operation_type"] = "Доход"
            return 1

        elif oper_type == "consumption":
            await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"Вы выбрали тип - <b>Расход</b>\n\nТеперь напишите мне сумму платежа.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Отмена ⛔️",
                            callback_data="menu"
                        )]
                    ])
            )

            context.user_data["operation_type"] = "Расход"
            return 1
        else:
            await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"❗️ Произошла ошибка. Неверно выбран тип операции. Вернитесь в меню и попробуйте еще раз.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 🍺",
                            callback_data="menu"
                        )]
                    ])
            )

            return ConversationHandler.END

    @check_user_status
    async def _get_operation_amount(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        try:
            context.user_data["operation_amount"] = int(update.message.text.strip())
            table_id = context.user_data.get("active_table_id", "")
            
            if table_id != "":
                cats = Category.objects.filter(table=Table.objects.get(pk=table_id),type=context.user_data["operation_type"]).all()
                
                if len(cats) != 0:
                    cats_keyboard = []
                    for index in range(0, len(cats), 2):
                        try:
                            c1, c2 = cats[index: index + 2]
                            cats_keyboard.append([InlineKeyboardButton(text=f"{c1.name}", callback_data=f"choose_cat_{c1.id}"), InlineKeyboardButton(text=f"{c2.name}", callback_data=f"choose_cat_{c2.id}")])
                        
                        except ValueError:
                            c1 = cats[index: index + 2][0]
                            cats_keyboard.append([InlineKeyboardButton(text=f"{c1.name}", callback_data=f"choose_cat_{c1.id}"),])
                    
                    cats_keyboard.append([
                        InlineKeyboardButton(
                                text="Отмена ⛔️",
                                callback_data="menu"
                        )
                    ])

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"🥶 Отлично, фиксируем сумму = <b>{int(update.message.text.strip())}₽</b> \n\nТеперь выберите категорию вашего платежа.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup(cats_keyboard)
                    )

                    return 2

                else:
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"🥶 Отлично, фиксируем сумму = <b>{int(update.message.text.strip())}₽</b> \n\n😶‍🌫️ К сожалению, у вас нет ни одной категории, подключенной к этой таблице. Вы можете добавить ее в главном меню.\n\n👁 А сейчас отравьте мне описание данной операции или нажмите на кнопку 'Пропустить ⏩'.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="Пропустить ⏩",
                                callback_data="skip_description"
                            )],
                            [InlineKeyboardButton(
                                text="Отмена ⛔️",
                                callback_data="menu"
                            )]
                        ])
                    )

                    return 3
                
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"❌ У вас не выбрана активная таблица. Выберите ее в меню и попробуйте еще раз.",
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

    @check_user_status
    async def _choose_operation_category(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        category_id = update.callback_query.data.split("_")[-1]
        if Category.objects.filter(id=category_id).exists():
            context.user_data["category_id"] = category_id
            
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Отлично! Категория <b>{Category.objects.get(pk=category_id).name}</b> выбрана.\n\n😃 Теперь напишите описание платежа или нажмите кнопку 'Пропустить ⏩' и на этом закончим.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Пропустить ⏩",
                        callback_data="skip_description"
                    )],
                    [InlineKeyboardButton(
                        text="Отмена ⛔️",
                        callback_data="menu"
                    )]
                ])
            )
            return 3
        
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"⛔️ Категории с выбранным <b>id</b> не существует.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    )]
                ])
            )
        
        return ConversationHandler.END

    @check_user_status
    async def _create_operation(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        
        try:
            desc = update.message.text.strip()
        except:
            desc = None

        table_id = context.user_data.get("active_table_id",'')

        if Table.objects.filter(id=table_id).exists():
            if Table.objects.get(pk=table_id) in usr.get_tables():
                try:
                    if context.user_data.get("category_id", "") != "":
                        cat = Category.objects.get(pk=context.user_data.get("category_id", None))
                    else:
                        cat = None

                    operation_type = context.user_data["operation_type"]
                    amount = context.user_data["operation_amount"]

                    new_operation = Operation(
                        type=operation_type,
                        amount=amount,
                        description=desc,
                        creator=usr,
                        category=cat,
                        table=Table.objects.get(pk=table_id)
                    )

                    new_operation.save()

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"✅ Операция с типом <b>{operation_type}</b> успешно добавлена.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="Добавить еще 🔃",
                                callback_data="add_operation",
                            )],
                            [InlineKeyboardButton(
                                text="В меню 🍺",
                                callback_data="menu"
                            )]
                        ])
                    )

                    return ConversationHandler.END

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

    def register_handlers(self) -> None: 
        """
            Метод реализующий регистрацию хэндлеров в приложении по операциям
        """

        # хэндлер для добавления операции в активную таблицу
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_operation_type, "add_operation")],
            states={
                0: [CallbackQueryHandler(self._add_operation, "^operation_")],
                1: [MessageHandler(filters.TEXT, self._get_operation_amount)],
                2: [CallbackQueryHandler(self._choose_operation_category, "^choose_cat_"),],
                3: [MessageHandler(filters.TEXT, self._create_operation), CallbackQueryHandler(self._create_operation, "skip_description")]

            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))
        
class CategoryWork(Bot):
    """
        Класс, инициализирующий instance класса для работы с категориями
    """

    def __init__(self, application) -> None:
        self.application = application 
    
    @check_user_status
    async def _ask_for_category_name(update:Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)

        if usr.can_create_tables:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🖍 Напишите название новой категории.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Отменить ⛔️",
                        callback_data="menu"
                    )]
                ])
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

    @check_user_status
    async def _ask_for_category_type(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        category_name = update.message.text.strip()

        context.user_data["category_name"] = category_name
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🔫 Отлично! Запомним имя категории - <b>{category_name}</b>.\n\nТеперь выберите тип категории ниже.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Доходная ➕",
                    callback_data="category_income"
                )],
                [InlineKeyboardButton(
                    text="Расходная ➖",
                    callback_data="category_consumption"
                )],
                [InlineKeyboardButton(
                    text="Отменить ⛔️",
                    callback_data="menu"
                )]
            ])
        )
        
        return 1

    @check_user_status
    async def _create_category(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)

        table_id = context.user_data.get("active_table_id",'')
        if Table.objects.filter(id=table_id).exists():
            if Table.objects.get(pk=table_id) in usr.get_tables():
                try:
                    category_name = context.user_data["category_name"]

                    if update.callback_query.data.split("_")[-1] == "income":
                        category_type = "Доход"
                    else:
                        category_type = "Расход"

                    Category(
                        name=category_name,
                        table=Table.objects.get(pk=table_id),
                        type=category_type
                    ).save()

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"✅ Категория <b>{category_name}</b> с типом <i>{category_type}</i> успешно добавлена",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="Добавить еще категорию 🐋",
                                callback_data="add_category",
                            )],
                            [InlineKeyboardButton(
                                text="В меню 🍺",
                                callback_data="menu"
                            ),]
                        ])
                    )

                except Exception as e:
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"❌ Не удалось добавить категорию.\n\n<b>Ошибка:</b><i>{e}</i>",
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

    @check_user_status
    async def _ask_category_to_change(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        table_id = context.user_data.get("active_table_id", "")
            
        if table_id != "":
            active_table = Table.objects.get(pk=table_id)
            cats = Category.objects.filter(table=active_table).all()

            if len(cats) != 0:
                cats_keyboard = []
                for index in range(0, len(cats), 2):
                    try:
                        c1, c2 = cats[index: index + 2]
                        cats_keyboard.append([InlineKeyboardButton(text=f"{c1.name}", callback_data=f"change_cat_{c1.id}"), InlineKeyboardButton(text=f"{c2.name}", callback_data=f"choose_cat_{c2.id}")])
                    
                    except ValueError:
                        c1 = cats[index: index + 2][0]
                        cats_keyboard.append([InlineKeyboardButton(text=f"{c1.name}", callback_data=f"change_cat_{c1.id}"),])
                
                cats_keyboard.append([
                    InlineKeyboardButton(
                            text="Отмена ⛔️",
                            callback_data="menu"
                    )
                ])

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🥴 Выберите категорию, которую хотите изменить, из списка ниже.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(cats_keyboard)
                )

                return 0

            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🥶 У вас не создано ни одной категории для изменения. Пожалуйста, создайте ее в главном меню.",
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
                f"🍔 <b>{usr.username}</b>, вы не выбрали активную таблицу.\n\n🧩 Пожалуйста, вернитесь в меню и выберите таблицу. ",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    ),]
                ])
            )

        return ConversationHandler.END   

    @check_user_status
    async def _ask_category_to_delete(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)

        table_id = context.user_data.get("active_table_id", "")
            
        if table_id != "":
            active_table = Table.objects.get(pk=table_id)
            cats = Category.objects.filter(table=active_table).all()

            if len(cats) != 0:
                cats_keyboard = []
                for index in range(0, len(cats), 2):
                    try:
                        c1, c2 = cats[index: index + 2]
                        cats_keyboard.append([InlineKeyboardButton(text=f"{c1.name}", callback_data=f"delete_cat_{c1.id}"), InlineKeyboardButton(text=f"{c2.name}", callback_data=f"delete_cat_{c2.id}")])
                    
                    except ValueError:
                        c1 = cats[index: index + 2][0]
                        cats_keyboard.append([InlineKeyboardButton(text=f"{c1.name}", callback_data=f"delete_cat_{c1.id}"),])
                
                cats_keyboard.append([
                    InlineKeyboardButton(
                            text="Отмена ⛔️",
                            callback_data="menu"
                    )
                ])

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🥴 Выберите категорию, которую хотите удалить, из списка ниже.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup(cats_keyboard)
                )

                return 0

            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🥶 У вас не создано ни одной категории для удаления. Пожалуйста, создайте ее в главном меню.",
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
                f"🍔 <b>{usr.username}</b>, вы не выбрали активную таблицу.\n\n🧩 Пожалуйста, вернитесь в меню и выберите таблицу. ",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    ),]
                ])
            )

        return ConversationHandler.END   

    @check_user_status
    async def _ask_category_name_to_change(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        context.user_data["category_id_to_change"] = update.callback_query.data.split("_")[-1]
        await context.bot.send_message(
            usr.telegram_chat_id, 
            f"😽 <b>Отлично!</b> Вы выбрали категорию - <i>{Category.objects.get(pk=context.user_data['category_id_to_change'])}</i>.\n\n👽 Теперь напишите мне новое <b>название</b> для выбранной категории.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Отмена ⛔️",
                    callback_data="menu"
                )]
            ])
        )

        return 1

    @check_user_status
    async def _delete_category(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        try:
            cat_to_delete = Category.objects.get(pk=update.callback_query.data.split("_")[-1])
            cat_to_delete_name = cat_to_delete.name
            cat_to_delete.delete()

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"😵‍💫 <b>Сделано!</b> Категория <b>{cat_to_delete_name}</b> успешно удалена.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    ),]
                ])
            )

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"😳 Во время изменения категории возникла ошибка.\n\n<b>Ошибка:</b> <i>{e}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    ),]
                ])
            )
        
        return ConversationHandler.END

    @check_user_status
    async def _update_category(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        new_name = update.message.text.strip()
        try:
            Category.objects.filter(id=context.user_data["category_id_to_change"]).update(
                name=new_name
            )

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Вы успешно изменили название категории на <b>{new_name}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    ),]
                ])
            )

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"😳 Во время изменения категории возникла ошибка.\n\n<b>Ошибка:</b> <i>{e}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🍺",
                        callback_data="menu"
                    ),]
                ])
            )
        
        return ConversationHandler.END

    def register_handlers(self) -> None: 
        """
            Метод реализующий регистрацию хэндлеров в приложении по операциям
        """

        # хэндлер для добавления категории в активную таблицу
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_category_name, "add_category")],
            states={
                0: [MessageHandler(filters.TEXT, self._ask_for_category_type)],
                1: [CallbackQueryHandler(self._create_category, "^category_")]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))    

        # хэндлер для изменения категории
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_category_to_change, "change_category")],
            states={
                0:[CallbackQueryHandler(self._ask_category_name_to_change, "^change_cat_")],
                1:[MessageHandler(filters.TEXT, self._update_category)]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

        # хэндлер для удаления категории
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_category_to_delete, "delete_category")],
            states={
                0:[CallbackQueryHandler(self._delete_category, "^delete_cat_")],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

class HistoryWork(Bot):
    """
        Класс, инициализирующий instance класса для работы с категориями
    """

    def __init__(self, application) -> None:
        self.application = application 

    @check_user_status
    async def _ask_for_history_type(update: Update, context: CallbackContext):
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

    @check_user_status
    async def _show_history(update: Update, context: CallbackContext):
        usr, _, _ = await user_get_by_update(update)
        table_id = context.user_data.get("active_table_id",'')

        message = list(filter(lambda x: x != " ", update.message.text.lower().strip().split()))
        expression = re.compile("(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[012])-(19|20)\d\d")

        if len(message) == 2:
            if expression.match(message[0]) and expression.match(message[1]):
                date_start, date_end = "-".join(reversed(message[0].split("-"))), "-".join(list(reversed(message[1].split("-")[1:])) + [str(int(message[1].split("-")[0]) + 1)])
                context.user_data["date_start"], context.user_data["date_end"] = date_start, date_end

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
                                        text="Анализ категорий 🦍",
                                        callback_data="analyse_history"
                                    )],
                                    [InlineKeyboardButton(
                                        text="Графический анализ 📊",
                                        callback_data="graph_history"
                                    )],
                                    [InlineKeyboardButton(
                                        text="Еще раз 🚀",
                                        callback_data="operation_history"
                                    ),
                                    InlineKeyboardButton(
                                        text="В меню 🍺",
                                        callback_data="menu"
                                    )],
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
    
    def register_handlers(self) -> None: 
        """
            Метод реализующий регистрацию хэндлеров в приложении по операциям
        """
        # хэндлер для добавления отображения истории
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_history_type, "operation_history")],
            states={
                0: [MessageHandler(filters.TEXT, self._show_history)]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

class GraphWork(Bot):
    """
        Класс описывающий работу с графиками по анализу дохода/расхода
    """        

    def __init__(self, application) -> None:
        self.application = application 

    @check_user_status
    async def _generate_graph(update: Update, context: CallbackContext) -> None:
        """
            Функция для генерации графика по последним 3 неделям пользователя
        """
        usr, _, _ = await user_get_by_update(update)
        table_id = context.user_data.get("active_table_id",'')

        curr_delta = (datetime.strptime(context.user_data["date_start"], '%Y-%m-%d').date(), datetime.strptime(context.user_data["date_end"], '%Y-%m-%d').date())
        time_delta = (curr_delta[1] - curr_delta[0]).days 

        delta_1 = (curr_delta[0] - timedelta(days=time_delta), curr_delta[1] - timedelta(days=time_delta))
        delta_2 = (delta_1[0] - timedelta(days=time_delta), delta_1[1] - timedelta(days=time_delta))

        if Table.objects.filter(id=table_id).exists():
            if Table.objects.get(pk=table_id) in usr.get_tables():
                users_table = Table.objects.get(pk=table_id)
                
                try:
                    data = {
                        "Расход": [0, 0, 0],
                        "Доход": [0, 0, 0],
                    }

                    # TODO я это писал под героином, надо переписать))

                    for index, week in enumerate([
                        Operation.objects.filter(
                        date__range=[curr_delta[0], curr_delta[1]],
                        table=users_table
                        ).all().order_by('-date'),

                        Operation.objects.filter(
                        date__range=[delta_1[0], delta_1[1]],
                        table=users_table
                        ).all().order_by('-date'),

                        Operation.objects.filter(
                        date__range=[delta_2[0], delta_2[1]],
                        table=users_table
                        ).all().order_by('-date'),
                    ]):
                        income, consumption = 0, 0
                        for operation in week:
                            if operation.type.lower() == "доход":
                                income += operation.amount
                            else:
                                consumption += operation.amount

                        data["Доход"][index] = income
                        data["Расход"][index] = consumption
                        

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"👽 <b>{usr.username}</b>, готовлю графический анализ...",
                        parse_mode="HTML",
                    )


                    weeks = ('Текущий период', 'Прошлый период', 'Позапрошлый период')
                    width = 0.4
                    bottom = np.zeros(len(weeks))

                    fig, ax = plt.subplots()

                    for money_type, money_count in data.items():
                        p = ax.bar(weeks, money_count, width, label=money_type, bottom=bottom)
                        bottom += money_count

                        ax.bar_label(p, label_type='center')

                    ax.set_title(f'Распределение доход/расход за последние 3 периода по {time_delta} дней')
                    ax.legend()

                    buf = io.BytesIO()
                    fig.savefig(buf)
                    buf.seek(0)
                    im = buf.getvalue()

                    await context.bot.send_photo(
                        usr.telegram_chat_id,
                        im, 
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


    def register_handlers(self) -> None: 
        """
            Метод реализующий регистрацию хэндлеров в приложении по операциям
        """
        # хэндлер для добавления отображения истории
        self.application.add_handler(CallbackQueryHandler(self._generate_graph, "graph_history"))

class Command(BaseCommand):
    help = 'Команда запуска телеграм бота'

    def handle(self, *args, **kwargs):        
        main_class_instance = Bot()
        application = main_class_instance.register_handlers()
        
        TableWork(application=application).register_handlers()
        OperationWork(application=application).register_handlers()
        CategoryWork(application=application).register_handlers()
        HistoryWork(application=application).register_handlers()
        GraphWork(application=application).register_handlers()

        application.add_handler(CallbackQueryHandler(main_class_instance._start, "menu"))
        
        application.run_polling()

        
        
        
