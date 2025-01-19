from ..applier_bot import ApplierBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class Auth(ApplierBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
    
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
                        text="💎 В меню",
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
                        text="✔️ Подтвердить",
                        callback_data="accept_sending_to_admin",
                    )],
                    [InlineKeyboardButton(
                        text="⛔️ Отмена",
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
                            text="💎 В меню",
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
            admin = ApplyUser.objects.filter(telegram_username=os.environ.get("ADMIN_TO_APPLY_telegram_username")).first()

            try:
                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"🤩 <b>{usr.telegram_telegram_username}</b>, здарова админ ебаный!\nНовая заявка в бота.\n\nНикнейм: <b>{usr.telegram_telegram_username}</b>\n\n<b>Инфа:</b>{usr.info if usr.info != None else 'Нет информации.'}\n\nПоинтересуйся у старших, есть такой или нет.",
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
                    f"🛜 <b>{usr.telegram_telegram_username}</b>, ваша заявка на вход отправлена. Ожидайте уведомления.",
                    parse_mode="HTML",
                )

            except Exception as e:
                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 В начало",
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
            
            token = Token.objects.get_or_create(user=user_to_apply)
            
            try:
                user_to_apply.update(
                    verified_usr=True
                )

                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"✅ Вы приняли пользователя <b>{user_to_apply.first().telegram_username}</b>.\n\n💰 Теперь укажите комиссию, которую мы даем пользователю.",
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
                    f"💘 Вы послали нахуй пользователя <b>{user_to_apply.first().telegram_username}</b>",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_apply.first().telegram_chat_id,
                    f"💔 <b>{user_to_apply.first().telegram_username}</b>, к сожалению, мы не можем принять вашу заявку!",
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
                f"✅ Вы успешно установили пользователю <b>{user.telegram_username}</b> комиссию в размере - <b>{comission}%</b>.",
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
                f"❤️‍🔥 <b>{user.telegram_username}</b>, ваша заявка успешно принята!\nВаша комиссия составит: <b>{user.comission}%</b>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 В меню",
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
                            text="💎 В меню",
                            callback_data="menu",
                        )],
                ])
            )

            return ConversationHandler.END

    def reg_handlers(self):
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