from applier.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, re, random, io, shutil, validators, secrets
warnings.filterwarnings("ignore")

import requests, base58

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

    instance, created = ApplyUser.objects.update_or_create(
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

        usr, _ = ApplyUser.objects.update_or_create(
            telegram_chat_id = message.chat.id,
            username=username
        )

        if usr.verified_usr:
            return await function(update, context)
            
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 <b>{usr.username}</b>, добрый день, если хотите отправить заявку на прием платежей, нажмите кнопку ниже.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Отправить заявку 🤘🏻",
                        callback_data="create_apply",
                    )]
                ])
            )
        
    return wrapper

class ApplierBot:
    
    def __init__(self) -> None:
        """"
            Инициализация апа
        """
        self.application = Application.builder().token(os.environ.get('APPLIER_BOT_TOKEN')).build()

    @check_user_status
    async def _start(update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)

        if not usr.is_superuser:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 <b>{usr.username}</b>, добрый день!\n\n💎 Ваш баланс: <b>{usr.balance}₽</b>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Отправить чек 💰",
                        callback_data="send_cheque",
                    )],
                    [InlineKeyboardButton(
                        text="Запросить вывод ⚡️",
                        callback_data="get_money",
                    )]
                ])
            )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 <b>{usr.username}</b>, здарова админ ебаный!",
                parse_mode="HTML",
                reply_markup = None
            )

        return ConversationHandler.END
    
    async def _send_apply_to_admin(self, update: Update, context: CallbackContext) -> None:
        """Функция отправки заявки админу

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)       
        
        if not usr.verified_usr:
            admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()

            try:
                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"🤩 <b>{usr.username}</b>, здарова админ ебаный!\nНовая заявка в бота.\n\nНикнейм: <b>{usr.username}</b>\n\nПоинтересуйся у старших, есть такой или нет.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Принять юзера ✅",
                            callback_data=f"acception_user_true_{usr.telegram_chat_id}",
                        )], 
                        [InlineKeyboardButton(
                            text="Пошел он нахуй ⛔️",
                            callback_data=f"acception_user_false_{usr.telegram_chat_id}",
                        )]
                    ])
                )

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🛜 <b>{usr.username}</b>, ваша заявка на вход отправлена. Ожидайте уведомления.",
                    parse_mode="HTML",
                )

            except Exception as e:
                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В начало 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )

    @check_user_status
    async def _new_user_acception(update: Update, context: CallbackContext) -> None:
        """Функция подтверждения/отмены принятия пользователя

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        query = update.callback_query
        await query.answer()
        
        user_id, status = query.data.split("_")[-1], query.data.split("_")[-2]
        user_to_apply = ApplyUser.objects.filter(telegram_chat_id=user_id)      
        if status == "true":

            try:
                user_to_apply.update(
                    verified_usr=True
                )

                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"✅ Вы приняли пользователя <b>{user_to_apply.first().username}</b>",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_apply.first().telegram_chat_id,
                    f"❤️‍🔥 <b>{user_to_apply.first().username}</b>, ваша заявка успешно принята!",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )
                
            except Exception as e:
                 await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"💔 Возникла ошибка во время доавления пользователя в семью.\n\n<i>{e}</i>",
                    parse_mode="HTML",
                )
        else:
            try:
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"💘 Вы послали нахуй пользователя <b>{user_to_apply.first().username}</b>",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_apply.first().telegram_chat_id,
                    f"💔 <b>{user_to_apply.first().username}</b>, к сожалению, мы не можем принять вашу заявку!",
                    parse_mode="HTML",
                )
                

            except Exception as e:
                 await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"💔 Возникла ошибка во время посылания нахуй пользователя.\n\n<i>{e}</i>",
                    parse_mode="HTML",
                )

    @check_user_status
    async def _ask_for_cheque_amount(update: Update, context: CallbackContext) -> None:
        """Функция прошения суммы

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"♾️ Супер, для начала напиши сумму чека.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Отменить ⛔️",
                    callback_data="menu",
                )],
            ])
        )
        
        return 0

    @check_user_status
    async def _ask_for_photo(update: Update, context: CallbackContext) -> None:
        """Функция прошения фото чека

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        usr, _ = await user_get_by_update(update)
        
        try:
            context.user_data["cheque_amount"] = int(update.message.text.strip())
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✔️ Теперь пришлите чек.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Отменить ⛔️",
                        callback_data="menu",
                    )],
                ])
            )

            return 1

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🟥 Возникла ошибка.\n\nОшибка: <i>{e}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                            text="В меню 💎",
                            callback_data="menu",
                        )],
                ])
            )
            return ConversationHandler.END

    @check_user_status
    async def _send_photo_to_admin(update: Update, context: CallbackContext) -> None:
        """Функция пересылки сообщения админу

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        usr, _ = await user_get_by_update(update)
        admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()

        await context.bot.forward_message(
            chat_id=admin.telegram_chat_id,
            from_chat_id=usr.telegram_chat_id,
            message_id=update.message.message_id
        )

        await context.bot.send_message(
            admin.telegram_chat_id,
            f"🤩 Новая оплата от <b>{usr.username}</b> на сумму {context.user_data.get('cheque_amount')} рублей.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Принять оплату чека ✅",
                    callback_data=f"acception_cheque_true_{context.user_data.get('cheque_amount')}_{usr.telegram_chat_id}",
                )], 
                [InlineKeyboardButton(
                    text="Пошел он нахуй ⛔️",
                    callback_data=f"acception_cheque_false_{context.user_data.get('cheque_amount')}_{usr.telegram_chat_id}",
                )]
            ])
        )

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"💊 Ваш чек отправлен.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🔰",
                    callback_data=f"menu",
                )], 
                
            ])
        )

        return ConversationHandler.END

    @check_user_status
    async def _new_cheque_acception(update: Update, context: CallbackContext) -> None:
        """Функция подтверждения/отмены принятия xtrf

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        query = update.callback_query
        await query.answer()
        
        user_id, amount, status = query.data.split("_")[-1], query.data.split("_")[-2], query.data.split("_")[-3] 
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        try:
            cheque_id = secrets.token_urlsafe(5)
            new_cheque = Cheque(
                cheque_id=f"#{cheque_id}",
                cheque_sum=int(amount),
                cheque_owner=ApplyUser.objects.filter(telegram_chat_id=user_id).first()
            )
            new_cheque.save()
            user_to_update = ApplyUser.objects.filter(telegram_chat_id=user_id).first()
                
            if status == "true":
                new_cheque.is_applied = True
                user_to_update.balance += int(amount)
                user_to_update.save()

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🪛 Вы приняли чек <b>#{cheque_id}</b>",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_update.telegram_chat_id,
                    f"🧲 Ваш чек <b>#{cheque_id}</b> принят.\nБаланс обновлен.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )

            else:
                new_cheque.is_denied = True
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"⚔️ Вы отклонили чек <b>#{cheque_id}</b>",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_update.telegram_chat_id,
                    f"🚬 Ваш чек <b>#{cheque_id}</b> был отклонен.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )

            new_cheque.save()
        
        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"💣 Возникла ошибка.\n\nОшибка: <i>{e}</i>",
                parse_mode="HTML",
            )

    @check_user_status
    async def _ask_for_money_withdraw(update: Update, context: CallbackContext) -> None:
        """Функция формирования заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        
        if int(usr.balance) >= 5000:
            try:
                url = "https://api.binance.com/api/v3/ticker/price"
                params = {
                    "symbol": "USDTRUB"
                }
                response = requests.get(url, params=params)
                ticker_info = response.json()

                if 'price' in ticker_info:
                    context.user_data["usdt_price"] = round(float(ticker_info['price']), 2) + float(os.environ.get("NADBAVKA"))
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"🤩 Отправьте свой адрес для приема <b><u>USDT</u></b> в сети <b><u>TRC20</u></b>.\n\nВАЖНО!! Если вы введете неверный адрес, то ваши средства могут быть утеряны.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="Отмена 💔",
                                callback_data="menu",
                            )],
                        ])
                    )

                    return 0

                else:
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"⛔️ Возникла ошибка во время получения цены <b>USDT/RUB</b>.\n\nЕсли проблема повторяется, обратитеь к администратору.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                    text="В меню 💎",
                                    callback_data="menu",
                            )],
                            [InlineKeyboardButton(
                                    text="Администратор 🆘",
                                    url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                            )],
                        ])
                    )

            except Exception as e:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"⛔️ Возникла ошибка во время получения цены <b>USDT/RUB</b>.\n\nОшибка: <i>{e}</i>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                                text="В меню 💎",
                                callback_data="menu",
                        )],
                        [InlineKeyboardButton(
                                text="Администратор 🆘",
                                url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                        )],
                    ])
                )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🟥 К сожалению, вы не можете вывести менее <b>5000₽</b>.\n\nЕсли у вас срочное обращение, то нажмите на кнопку ниже и обратитель к админиcтартору.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                            text="В меню 💎",
                            callback_data="menu",
                    )],
                    [InlineKeyboardButton(
                            text="Администратор 🆘",
                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                    )],
                ])
            )

            return ConversationHandler.END

    @check_user_status
    async def _send_withdraw_appliment(update: Update, context: CallbackContext) -> None:
        """Функция для подтверждения заявки для вывода

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        usdt_address = update.message.text.strip()

        def is_trc20_address(address):
            if len(address) != 34:
                return False
            if address[0] != 'T':
                return False
            try:
                decoded = base58.b58decode_check(address)
                if len(decoded) == 21:
                    return True
            except ValueError:
                return False
            return False

        if is_trc20_address(usdt_address):
            context.user_data['usdt_address'] = usdt_address
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"Вы отравили неверный адрес. Проверьте, что вы отправили адрес <b>USDT</b> в сети <b>TRC-20</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🚬",
                        callback_data="menu",
                    )],
                ])
            )
            return ConversationHandler.END

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"Вы запросили вывод:\n\n✔️ Сумма: <b>{usr.balance}₽</b>\n✔️ Курс: <b>{context.user_data['usdt_price']}₽</b>\n✔️ Адрес TRC-20: <i>{context.user_data['usdt_address']}₽</i>\n\nИтог: <b><u>{round(usr.balance / context.user_data['usdt_price'], 2)} USDT</u></b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                        text="Подтверждаю ✅",
                        callback_data="apply_withdraw",
                )],
                [InlineKeyboardButton(
                        text="Отменить ❌",
                        callback_data="menu",
                )],
            ])
        )

        return ConversationHandler.END

    @check_user_status
    async def _send_withdraw_appliment_to_admin(update: Update, context: CallbackContext) -> None:
        """Функция для отправки админу заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        query = update.callback_query
        await query.answer()
        
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        try:
            admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()
            
            order = Withdraw(
                withdraw_id = f"#{secrets.token_urlsafe(5)}",
                withdraw_sum = usr.balance,
                withdraw_owner=usr,
                withdraw_address=context.user_data["usdt_address"],
                course=context.user_data["usdt_price"],
                usdt_sum=round(usr.balance / context.user_data["usdt_price"], 2),
            )

            order.save()

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🛜 <b>{usr.username}</b>, ваша заявка <b>{order.withdraw_id}</b> на вывод отправлена. Ожидайте уведомления.",
                parse_mode="HTML",
            )

            await context.bot.send_message(
                admin.telegram_chat_id,
                f"<b>{usr.username}</b> запросил вывод <b>{order.withdraw_id}</b>:\n\n✔️ Сумма: <b>{usr.balance}₽</b>\n✔️ Курс: <b>{context.user_data['usdt_price']}₽</b>\n✔️ Адрес TRC-20: <i>{context.user_data['usdt_address']}₽</i>\n\nИтог: <b><u>{round(usr.balance / context.user_data['usdt_price'], 2)} USDT</u></b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Ордер оплачен ✅",
                        callback_data=f"order_paid_{usr.telegram_chat_id}_{order.withdraw_id}",
                    )],
                ])
            )

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В начало 🔰",
                        callback_data=f"menu",
                    )], 
                    [InlineKeyboardButton(
                        text="Администратор 🆘",
                        url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                    )],
                ])
            )

    @check_user_status
    async def _apply_withdraw_appliment(update: Update, context: CallbackContext) -> None:
        """Функция для принятия заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        query = update.callback_query
        await query.answer()
        
        user_id, withdraw_id = query.data.split("_")[-2], query.data.split("_")[-1] 
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        try:
            order = Withdraw.objects.filter(withdraw_id=withdraw_id)
            order.update(
                is_applied=True
            )

            order = order.first()
            user_whom_applied = ApplyUser.objects.filter(telegram_chat_id=user_id).first()
            
            user_whom_applied.balance = 0
            user_whom_applied.save()

            await context.bot.send_message(
                user_whom_applied.telegram_chat_id,
                f"✅ <b>{user_whom_applied.username}</b>, ваш ордер <b>{order.withdraw_id}</b> на сумму <b>{order.usdt_sum} USDT</b> оплачен.\n\nЕсли у вас возникли какие-то вопросы, то обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🔰",
                        callback_data=f"menu",
                    )], 
                    [InlineKeyboardButton(
                        text="Администратор 🆘",
                        url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                    )],
                    
                ])
            )

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В начало 🔰",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )


    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """
        self.application.add_handler(CommandHandler("start", self._start))
        self.application.add_handler(CallbackQueryHandler(self._send_apply_to_admin, "create_apply"))
        self.application.add_handler(CallbackQueryHandler(self._new_user_acception, "^acception_user_"))
        self.application.add_handler(CallbackQueryHandler(self._new_cheque_acception, "^acception_cheque_"))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_cheque_amount, "send_cheque")],
            states={
                0: [MessageHandler(filters.TEXT, self._ask_for_photo)],
                1: [MessageHandler(filters.PHOTO, self._send_photo_to_admin)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_money_withdraw, "get_money")],
            states={
                0: [MessageHandler(filters.TEXT, self._send_withdraw_appliment)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

        self.application.add_handler(CallbackQueryHandler(self._send_withdraw_appliment_to_admin, "apply_withdraw"))
        self.application.add_handler(CallbackQueryHandler(self._apply_withdraw_appliment, "^order_paid_"))

        return self.application

class Command(BaseCommand):
    help = 'Команда запуска ApplyBot'

    def handle(self, *args, **kwargs):        
        main_class_instance = ApplierBot()
        application = main_class_instance.register_handlers()
        
        application.add_handler(CallbackQueryHandler(main_class_instance._start, "menu"))
        application.run_polling()