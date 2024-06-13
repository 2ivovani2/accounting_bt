from applier.models import *

from asgiref.sync import sync_to_async

import time
from typing import TypedDict, List, Literal, cast
import requests, base58
import os, django, logging, warnings, secrets
warnings.filterwarnings("ignore")

from django.core.management.base import BaseCommand

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
    InputMediaPhoto,
    InputMediaDocument,
)

from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ApplicationBuilder,
    PicklePersistence,
)
from telegram.helpers import effective_message_type

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
        async def post_init(application: Application):
            if "messages" not in application.bot_data:
                application.bot_data = {"messages": {}}

        self.application = (
            ApplicationBuilder()
            .token(os.environ.get('APPLIER_BOT_TOKEN'))
            .post_init(post_init)
            .build()
        )
       
    async def _start(self, update: Update, context: CallbackContext):
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)
        

        if not usr.verified_usr:
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
        else:
            if not usr.is_superuser:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🤩 <b>{usr.username}</b>, добрый день!\n\n💎 Ваш баланс: <b>{usr.balance}₽</b>\n💰 Ваша комиссия составляет: <b>{usr.comission}%</b>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Отправить чек 💰",
                            callback_data="send_cheque",
                        )],
                        [InlineKeyboardButton(
                            text="Запросить крипто вывод ⚡️",
                            callback_data="get_money_crypto",
                        )], 
                        [InlineKeyboardButton(
                            text="Запросить фиат вывод 💳",
                            callback_data="get_money_fiat",
                        )], 
                        [InlineKeyboardButton(
                            text="Операции за сегодня 📆",
                            callback_data="today_hist",
                        )],
                    ])
                )
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🤩 <b>{usr.username}</b>, здарова админ <b>ЕБАНЫЙ</b>!",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Статистика 📊",
                            callback_data="stat",
                        )],
                        [InlineKeyboardButton(
                            text="Метрики дня ⭐️",
                            callback_data="metrics",
                        )],
                        # [InlineKeyboardButton(
                        #     text="Админка 👀",
                        #     web_app=WebAppInfo(url=f"{os.environ.get('DOMAIN_NAME')}/admin")
                        # )]
                    ])
                )

        return ConversationHandler.END
    
    async def _ask_for_info(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)

        await context.bot.send_photo(
            usr.telegram_chat_id,
            photo="https://i.ibb.co/b1Tj1Fw/photo-2024-06-01-21-05-33.jpg",
            caption=f"💷 Приветствую, <b>партнер!</b>\n\nОтветь на несколько вопросов, чтобы мы могли принять твою заявку ⬇️\n\n- Откуда ты хочешь лить деньги ( приват/скам/ реклама )\n- Напиши объем, который ты готов загонять на карты\n- Как ты узнал о DRIP MONEY\n\n<i>Скоро ответим, на твою заявку, с любовью команда <b>DRIP MONEY</b></i>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                        text="В меню 💎",
                        callback_data="menu",
                )],
            ])
        )

        return 0

    async def _set_user_info(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)
        info = update.message.text.strip()
        
        try:
            usr.info = info
            usr.save()
            
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Информацию учли, подтвердите отправку.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Подтвердить ✔️",
                        callback_data="accept_sending_to_admin",
                    )],
                    [InlineKeyboardButton(
                        text="Отмена ⛔️",
                        callback_data="menu",
                    )],
                ])
            )

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
        
        return 1

    async def _send_apply_to_admin(self, update: Update, context: CallbackContext) -> None:
        """Функция отправки заявки админу

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)       
        
        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        if not usr.verified_usr:
            admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()

            try:
                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"🤩 <b>{usr.username}</b>, здарова админ ебаный!\nНовая заявка в бота.\n\nНикнейм: <b>{usr.username}</b>\n\n<b>Инфа:</b>{usr.info if usr.info != None else 'Нет информации.'}\n\nПоинтересуйся у старших, есть такой или нет.",
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
        
        return ConversationHandler.END

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
                    f"✅ Вы приняли пользователя <b>{user_to_apply.first().username}</b>.\n\n💰 Теперь укажите комиссию, которую мы даем пользователю.",
                    parse_mode="HTML",
                )

                context.user_data["user_id_applied"] = user_to_apply.first().id
                
                return 0

            except Exception as e:
                 await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"💔 Возникла ошибка во время добавления пользователя в семью.\n\n<i>{e}</i>",
                    parse_mode="HTML",
                )
                
            return ConversationHandler.END
        
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
                 
            return ConversationHandler.END

    @check_user_status
    async def _set_comission(update: Update, context: CallbackContext) -> None:
        """Функция подтверждения/отмены принятия пользователя

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        try:
            user = ApplyUser.objects.get(pk=int(context.user_data["user_id_applied"]))
            comission = int(update.message.text)

            user.comission = comission
            user.save()

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Вы успешно установили пользователю <b>{user.username}</b> комиссию в размере - <b>{comission}%</b>.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                            text="В меню 💎",
                            callback_data="menu",
                    )],
                ])
            )

            await context.bot.send_message(
                user.telegram_chat_id,
                f"❤️‍🔥 <b>{user.username}</b>, ваша заявка успешно принята!\nВаша комиссия составит: <b>{user.comission}%</b>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🔰",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )

            return ConversationHandler.END

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
                f"✔️ Теперь пришлите чек(и).",
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
    async def _send_photo_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Функция пересылки сообщения админу

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()
        usr, _ = await user_get_by_update(update)
        
        MEDIA_GROUP_TYPES = {
            "document": InputMediaDocument,
            "photo": InputMediaPhoto,
        }
    
        class MsgDict(TypedDict):
            media_type: Literal["photo"]
            media_id: str
            caption: str
            post_id: int
    
        async def media_group_sender(cont: ContextTypes.DEFAULT_TYPE):
            bot = cont.bot
            cont.job.data = cast(List[MsgDict], cont.job.data)
            media = []
            for msg_dict in cont.job.data:
                media.append(
                    MEDIA_GROUP_TYPES[msg_dict["media_type"]](
                        media=msg_dict["media_id"], caption=msg_dict["caption"]
                    )
                )
            if not media:
                return
            
            msgs = await bot.send_media_group(chat_id=admin.telegram_chat_id, media=media)
            await cont.bot.send_message(
                admin.telegram_chat_id,
                f"🤩 Новая оплата от <b>{usr.username}</b> на сумму <b>{context.user_data.get('cheque_amount')}</b> рублей.",
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

            await cont.bot.send_message(
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
            for index, msg in enumerate(msgs):
                cont.bot_data["messages"][
                    cont.job.data[index]["post_id"]
                ] = msg.message_id
            
            return ConversationHandler.END

        message = update.effective_message
        if message.media_group_id:
            media_type = effective_message_type(message)
            media_id = (
                message.photo[-1].file_id
                if message.photo
                else message.effective_attachment.file_id
            )
            msg_dict = {
                "media_type": media_type,
                "media_id": media_id,
                "caption": message.caption_html,
                "post_id": message.message_id,
            }
            jobs = context.job_queue.get_jobs_by_name(str(message.media_group_id))
            if jobs:
                jobs[0].data.append(msg_dict)
            else:
                context.job_queue.run_once(
                    callback=media_group_sender,
                    when=2,
                    data=[msg_dict],
                    name=str(message.media_group_id),
                )
        else:
            await context.bot.forward_message(
                chat_id=admin.telegram_chat_id,
                from_chat_id=usr.telegram_chat_id,
                message_id=update.message.message_id
            )
         
            await context.bot.send_message(
                admin.telegram_chat_id,
                f"🤩 Новая оплата от <b>{usr.username}</b> на сумму <b>{context.user_data.get('cheque_amount')}</b> рублей.",
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
            context.bot_data["messages"][message.message_id] = msg.message_id

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
            user_to_update = ApplyUser.objects.filter(telegram_chat_id=user_id).first()

            cheque_id = secrets.token_urlsafe(int(os.environ.get("IDS_LEN")))
            new_cheque = Cheque(
                cheque_id=f"#{cheque_id}",
                cheque_sum=int(amount),
                cheque_owner=user_to_update,
                income=(int(amount) * user_to_update.comission * 0.01)
            )
            new_cheque.save()
                
            if status == "true":
                new_cheque.is_applied = True
                user_to_update.balance += int(amount) - (int(amount) * user_to_update.comission * 0.01)
                user_to_update.save()

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🪛 Вы приняли чек <b>#{cheque_id}</b> от <b>{new_cheque.cheque_owner.username}</b> на сумму <b>{new_cheque.cheque_sum}₽</b>.",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_update.telegram_chat_id,
                    f"🧲 Ваш чек <b>#{cheque_id}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> принят.\nБаланс обновлен.",
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
                    f"⚔️ Вы отклонили чек <b>#{cheque_id}</b> от <b>{new_cheque.cheque_owner.username}</b> на сумму <b>{new_cheque.cheque_sum}₽</b>.",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_update.telegram_chat_id,
                    f"🚬 Ваш чек <b>#{cheque_id}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> был отклонен.",
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
        query = update.callback_query
        await query.answer()
        
        type_of_withdraw = query.data.split("_")[-1]

        if int(usr.balance) >= int(os.environ.get("MIN_SUM_TO_WITHDRAW")):
            if type_of_withdraw == "crypto":
                context.user_data["withdraw_type"] = "crypto"

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
                context.user_data["withdraw_type"] = "fiat"
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"💳 Отправьте <b>номер карты</b> и через пробел <b>название банка</b>, куда необходимо произвести вывод.\n\nВАЖНО!! Если вы введете неверный номер, то ваши средства могут быть утеряны.",
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
        withdraw_type = context.user_data.get("withdraw_type", None)
        if withdraw_type == "crypto":
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
                f"Вы запросили вывод:\n\n✔️ Сумма: <b>{usr.balance}₽</b>\n✔️ Курс: <b>{context.user_data['usdt_price']}₽</b>\n✔️ Адрес TRC-20: <i>{context.user_data['usdt_address']}</i>\n\nИтог: <b><u>{round(usr.balance / context.user_data['usdt_price'], 2) - 2} USDT</u></b>\n\n* <i>2$ - комиссия на вывод USDT самой биржи.</i>",
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
        elif withdraw_type == "fiat":
            card_number = update.message.text.strip()
            context.user_data["card_number"] = card_number
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"Вы запросили вывод:\n\n✔️ Сумма: <b>{usr.balance}₽</b>\n💳 Реквизиты: <pre>{card_number}</pre>\n\n* <i>Может взиматься комиссия на вывод банков.</i>",
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
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🟥 К сожалению, не удается подтвердить информацию. Если ошибка повторяется, обратитесь к администратору.",
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
    async def _send_withdraw_appliment_to_admin(update: Update, context: CallbackContext) -> None:
        """Функция для отправки админу заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()
        
        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        withdraw_type = context.user_data.get("withdraw_type", None)
        if withdraw_type == "crypto":
            try: 
                order = Withdraw(
                    withdraw_id = f"#{secrets.token_urlsafe(int(os.environ.get('IDS_LEN')))}",
                    withdraw_sum = usr.balance,
                    withdraw_owner = usr,
                    withdraw_address = context.user_data["usdt_address"],
                    course = context.user_data["usdt_price"],
                    usdt_sum = round(usr.balance / context.user_data['usdt_price'], 2) - 2,
                )

                order.save()

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🛜 <b>{usr.username}</b>, ваша заявка <b>{order.withdraw_id}</b> на вывод отправлена. Ожидайте уведомления.",
                    parse_mode="HTML",
                )
                
                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"<b>{usr.username}</b> запросил вывод <b>{order.withdraw_id}</b>:\n\n✔️ Сумма: <b>{order.withdraw_sum}₽</b>\n✔️ Курс: <b>{context.user_data['usdt_price']}₽</b>\n✔️ Адрес TRC-20: <i>{context.user_data['usdt_address']}</i>\n\nИтог: <b><u>{order.usdt_sum} USDT</u></b>",
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
        elif withdraw_type == "fiat":
            try: 
                order = Withdraw(
                    withdraw_id = f"#{secrets.token_urlsafe(int(os.environ.get('IDS_LEN')))}",
                    withdraw_sum = usr.balance,
                    withdraw_owner = usr,
                    withdraw_card_number = context.user_data["card_number"],
                )

                order.save()

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🛜 <b>{usr.username}</b>, ваша заявка <b>{order.withdraw_id}</b> на вывод отправлена. Ожидайте уведомления.",
                    parse_mode="HTML",
                )
                
                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"<b>{usr.username}</b> запросил вывод <b>{order.withdraw_id}</b>:\n\n✔️ Сумма: <b>{order.withdraw_sum}₽</b>\n💳 Реквизиты: <pre>{order.withdraw_card_number}</pre>",
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
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🟥 К сожалению, не удается подтвердить информацию. Если ошибка повторяется, обратитесь к администратору.",
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
    async def _apply_withdraw_appliment(update: Update, context: CallbackContext) -> None:
        """Функция для принятия заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        query = update.callback_query
        await query.answer()
        
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        user_id, withdraw_id = query.data.split("_")[-2], query.data.split("_")[-1] 
        
        try:
            order = Withdraw.objects.filter(withdraw_id=withdraw_id)
            order.update(
                is_applied=True
            )

            order = order.first()
            user_whom_applied = ApplyUser.objects.filter(telegram_chat_id=user_id).first()
            
            user_whom_applied.balance -= order.withdraw_sum
            user_whom_applied.save()
            
            if order.withdraw_address:
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

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"👅 <b>{usr.username}</b>, вы успешно оплатили <b>{order.withdraw_id}</b> на сумму <b>{order.usdt_sum} USDT</b> от <b>{user_whom_applied.username}</b>.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 🔰",
                            callback_data=f"menu",
                        )], 
                    ])
                )
            else:
                await context.bot.send_message(
                    user_whom_applied.telegram_chat_id,
                    f"✅ <b>{user_whom_applied.username}</b>, ваш ордер <b>{order.withdraw_id}</b> на сумму <b>{order.withdraw_sum}₽</b> оплачен фиатом.\n\nЕсли у вас возникли какие-то вопросы, то обратитесь к администратору.",
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

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"👅 <b>{usr.username}</b>, вы успешно оплатили <b>{order.withdraw_id}</b> на сумму <b>{order.withdraw_sum}₽ фиатом</b> от <b>{user_whom_applied.username}</b>.",
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
    async def _ask_for_username_in_stat(update: Update, context: CallbackContext) -> None:
        """Получения юзернейма

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 Отправьте имя пользователя в формате <b>@username</b> или просто <b>username</b>.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 💎",
                        callback_data="menu",
                    )],
                ])
        )

        return 0

    @check_user_status
    async def _ask_for_stat(update: Update, context: CallbackContext) -> None:
        """Функция для получения статистики

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        username_to_get_stat = update.message.text.strip().replace("@", "")

        if not ApplyUser.objects.filter(username=username_to_get_stat).exists():
            await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"❌ Пользователя с таким юзернемом не существует.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 💎",
                            callback_data="menu",
                        )],
                    ])
                )

            return ConversationHandler.END
        else:
            context.user_data["username_stat"] = update.message.text.strip().replace("@", "")

            if usr.is_superuser:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🪛 Выберите операцию, которая вас интересует.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Стат за день ☀️",
                            callback_data="stat_day",
                        )], 
                        [InlineKeyboardButton(
                            text="Стат за все время ⏳",
                            callback_data="stat_all",
                        )],
                        [InlineKeyboardButton(
                            text="В меню 💎",
                            callback_data="menu",
                        )],
                    ])
                )

                return 1
            
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🆘 К сожалению, у вас недостаточно прав для выполнения данной операции.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В начало 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )

                return ConversationHandler.END

    @check_user_status
    async def _get_stat(update: Update, context: CallbackContext) -> None:
        """Функция для получения статистики

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        
        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        user_info_about = context.user_data.get("username_stat", None)
        if not user_info_about:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🆘 К сожалению, пользователь не найден, попробуйте еще раз.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В начало 🔰",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )
            return ConversationHandler.END

        type_of_oper = query.data.split("_")[-1]
        if type_of_oper == "day":

            cheques = Cheque.objects.filter(
                cheque_owner=ApplyUser.objects.filter(username=user_info_about).first(),
                cheque_date__date=timezone.now()
            ).all()

            withdraws = Withdraw.objects.filter(
                withdraw_owner=ApplyUser.objects.filter(username=user_info_about).first(),
                withdraw_date__date=timezone.now()    
            ).all()

            total_cheques_sum, total_withdraw_sum, total_income = 0, 0, 0
            end_msg = f"💰 Статистика о пользователе <b>{ApplyUser.objects.filter(username=user_info_about).first().username}</b> за сегодня:\n\n<b>Чеки:</b>\n"
            
            if len(cheques) == 0:
                end_msg += "🙁 Сегодня чеков не было.\n"
            else:
                for cheque in cheques:
                    if cheque.is_applied:
                        total_cheques_sum += cheque.cheque_sum
                        total_income += cheque.income

                    if not cheque.is_applied and not cheque.is_denied:
                        status = "В работе"
                    elif cheque.is_applied:
                        status = "Принят"
                    else:
                        status = "Не принят"
                
                    end_msg += f"<i>{cheque.cheque_id} - {cheque.cheque_sum}₽ - {status} - {cheque.income}₽</i>\n"
            
            end_msg += "\n<b>Выводы:</b>\n"

            if len(withdraws) == 0:
                end_msg += "🙁 Сегодня выводов не было.\n"
            else:
                for withdraw in withdraws:
                    if withdraw.is_applied:
                        total_withdraw_sum += withdraw.withdraw_sum

                    if not withdraw.is_applied:
                        status = "В работе"
                    elif withdraw.is_applied:
                        status = "Оплачен"
                    
                    end_msg += f"<i>{withdraw.withdraw_id} - {withdraw.withdraw_sum}₽ - {status} - {withdraw.usdt_sum}USDT</i>\n"
            
            end_msg += f"\nОбщая сумма по чекам: <b>{total_cheques_sum}₽</b>\nОбщая сумма по выводам: <b>{total_withdraw_sum}₽</b>\nОбщая прибыль: <b>{total_income}₽</b>"

            await context.bot.send_message(
                    usr.telegram_chat_id,
                    end_msg,
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В начало 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )
        
        elif type_of_oper == "all":
            cheques = Cheque.objects.filter(
                cheque_owner=ApplyUser.objects.filter(username=user_info_about).first(),
            ).all()

            withdraws = Withdraw.objects.filter(
                withdraw_owner=ApplyUser.objects.filter(username=user_info_about).first(),
            ).all()

            total_cheques_sum, total_withdraw_sum, total_income = 0, 0, 0
            end_msg = f"💰 Статистика о пользователе <b>{ApplyUser.objects.filter(username=user_info_about).first().username}</b> за все время:\n\n<b>Чеки:</b>\n"
            
            cnt1, cnt2 = 0, 0

            if len(cheques) == 0:
                end_msg += "🙁 Пока чеков не было."
            else:
                for cheque in cheques:
                    total_cheques_sum += cheque.cheque_sum

                    if not cheque.is_applied and not cheque.is_denied:
                        status = "В работе"
                    elif cheque.is_applied:
                        status = "Принят"
                    else:
                        status = "Не принят"

                    if not cnt1 == os.environ.get("CNT_TO_SHOW_STAT_FOR_ALL_TIME"):
                        end_msg += f"<i>{cheque.cheque_id} - {cheque.cheque_sum}₽ - {status}</i>\n"
                        cnt1 += 1

            end_msg += "\n<b>Выводы:</b>\n"

            if len(withdraws) == 0:
                end_msg += "🙁 Пока выводов не было."
            else:
                for withdraw in withdraws:
                    total_withdraw_sum += withdraw.withdraw_sum
                    total_income += withdraw.income

                    if not withdraw.is_applied:
                        status = "В работе"
                    elif withdraw.is_applied:
                        status = "Оплачен"
                    
                    if not cnt2 == os.environ.get("CNT_TO_SHOW_STAT_FOR_ALL_TIME"):
                        end_msg += f"<i>{withdraw.withdraw_id} - {withdraw.withdraw_sum}₽ - {status} - {withdraw.usdt_sum}USDT - {withdraw.income}₽</i>\n"
                        cnt2 += 1

            end_msg += f"\nОбщая сумма по чекам: <b>{total_cheques_sum}₽</b>\nОбщая сумма по выводам: <b>{total_withdraw_sum}₽</b>\nОбщая прибыль: <b>{total_income}₽</b>"

            await context.bot.send_message(
                    usr.telegram_chat_id,
                    end_msg,
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В начало 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )

        return ConversationHandler.END

    @check_user_status
    async def _today_metrics(update: Update, context: CallbackContext) -> None:
        """Функция для получения метрик за день для админа

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        total_trans, total_income, total_withdraws = 0, 0, 0

        cheques = Cheque.objects.filter(
            cheque_date__date=timezone.now()
        ).all()

        withdraws = Withdraw.objects.filter(
            withdraw_date__date=timezone.now()    
        ).all()

        for cheque in cheques:
            if cheque.is_applied:
                total_trans += int(cheque.cheque_sum)
                total_income += cheque.income

        for withdraw in withdraws:
            if withdraw.is_applied:
                total_withdraws += withdraw.withdraw_sum

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🌎 <b>Чеки:</b>\n- Общий оборот: <b>{total_trans}₽</b>\n- Прибыль: <b>{round(total_income, 2)}₽</b>\n- Всего чеков: <b>{len(cheques)} шт.</b>\n\n🌙 <b>Выводы:</b>\n- Общая сумма выводов: <b>{total_withdraws}₽</b>\n- Всего выводов: <b>{len(withdraws)} шт.</b>",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В начало 🔰",
                    callback_data=f"menu",
                )], 
                
            ])
        )

    @check_user_status
    async def _today_hist(update: Update, context: CallbackContext) -> None:
        """Функция для получения статистики за день для юзера

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        cheques = Cheque.objects.filter(
            cheque_owner=ApplyUser.objects.filter(username=usr).first(),
            cheque_date__date=timezone.now()
        ).all()

        withdraws = Withdraw.objects.filter(
            withdraw_owner=ApplyUser.objects.filter(username=usr).first(),
            withdraw_date__date=timezone.now()    
        ).all()

        total_cheques_sum, total_withdraw_sum = 0, 0
        end_msg = f"💰 Статистика за сегодня:\n\n<b>Чеки:</b>\n"
        
        if len(cheques) == 0:
            end_msg += "🙁 Сегодня чеков не было.\n"
        else:
            for cheque in cheques:
                if cheque.is_applied:
                    total_cheques_sum += cheque.cheque_sum

                if not cheque.is_applied and not cheque.is_denied:
                    status = "В работе"
                elif cheque.is_applied:
                    status = "Принят"
                else:
                    status = "Не принят"
            
                end_msg += f"<i>{cheque.cheque_id} - {cheque.cheque_sum}₽ - {status}</i>\n"
        
        end_msg += "\n<b>Выводы:</b>\n"

        if len(withdraws) == 0:
            end_msg += "🙁 Сегодня выводов не было.\n"
        else:
            for withdraw in withdraws:
                if withdraw.is_applied:
                    total_withdraw_sum += withdraw.withdraw_sum

                if not withdraw.is_applied:
                    status = "В работе"
                elif withdraw.is_applied:
                    status = "Оплачен"
                
                end_msg += f"<i>{withdraw.withdraw_id} - {withdraw.withdraw_sum}₽ - {status} - {withdraw.usdt_sum}USDT - {withdraw.income}₽</i>\n"
        
        end_msg += f"\nОбщая сумма по чекам: <b>{total_cheques_sum}₽</b>\nОбщая сумма по выводам: <b>{total_withdraw_sum}₽</b>"

        await context.bot.send_message(
                usr.telegram_chat_id,
                end_msg,
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

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_info, "create_apply")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._set_user_info)],
                1: [CallbackQueryHandler(self._send_apply_to_admin, "accept_sending_to_admin")]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._new_user_acception, "^acception_user_")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._set_comission)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(CallbackQueryHandler(self._new_cheque_acception, "^acception_cheque_"))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_cheque_amount, "send_cheque")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._ask_for_photo)],
                1: [MessageHandler(filters.PHOTO, self._send_photo_to_admin)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_money_withdraw, "^get_money_")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._send_withdraw_appliment)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_username_in_stat, "stat"), CommandHandler("stat", self._ask_for_username_in_stat)],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._ask_for_stat)],
                1: [CallbackQueryHandler(self._get_stat, "^stat_")]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(CallbackQueryHandler(self._send_withdraw_appliment_to_admin, "apply_withdraw"))
        self.application.add_handler(CallbackQueryHandler(self._apply_withdraw_appliment, "^order_paid_"))

        self.application.add_handler(CallbackQueryHandler(self._today_hist, "today_hist"))
        self.application.add_handler(CallbackQueryHandler(self._today_metrics, "metrics"))

        self.application.add_handler(CommandHandler("start", self._start))
        self.application.add_handler(CallbackQueryHandler(self._start, "menu"))

        return self.application

class Command(BaseCommand):
    help = 'Команда запуска ApplyBot'

    def handle(self, *args, **kwargs):        
    
        main_class_instance = ApplierBot()
        application = main_class_instance.register_handlers()
        
        application.add_handler(CallbackQueryHandler(main_class_instance._start, "menu"))
        application.run_polling()
