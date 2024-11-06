from ..processors_bot import ProcessorsBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class Auth(ProcessorsBot):
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
            caption=f"💷 Приветствую, <b>партнер!</b>\n\nОтветь на несколько вопросов, чтобы мы могли принять твою заявку ⬇️",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                        text="🚀 Поехали",
                        callback_data="start_questions",
                )],
            ])
        )

        return 0

    async def _ask_about_income_avaliable(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)
        
        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🍀 Какую сумму ты готов принимать на свои реквизиты, выбери из списка ниже?\n\n<blockquote>Если тут нет подходящей суммы, то при добавлении реквизитов, будет возможность ее изменить.</blockquote>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                        text="30k rub",
                        callback_data="ready_to_accept_30",
                )],
                [InlineKeyboardButton(
                        text="50k rub",
                        callback_data="ready_to_accept_50",
                )],
                [InlineKeyboardButton(
                        text="70k rub",
                        callback_data="ready_to_accept_70",
                )],
                [InlineKeyboardButton(
                        text="💎 В меню",
                        callback_data="menu",
                )],
            ])
        )

        return 1
    
    async def _ask_where_are_you_from(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)
        
        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        context.user_data["ready_to_accept"] = int(query.data.split("_")[-1]) * 1000

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"📰 Теперь <b>напиши</b> откуда узнал о нас и мы рассмотрим твою заявку.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                        text="💎 В меню",
                        callback_data="menu",
                )],
            ])
        )

        return 2

    async def _save_user_apply_and_send_to_admin(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)
        admin = Processor.objects.filter(username=os.environ.get("PROCESSORS_ADMIN_USERNAME", "i_vovani")).first()

        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        try:
            usr.info = update.message.text.strip()
            usr.amount_to_accept = context.user_data["ready_to_accept"]
            usr.save()

            message = await context.bot.send_message(
                admin.telegram_chat_id,
                f"😯 Новая заявка от процессора <b>{usr.username}</b> на вступление.\n\n🔴 Готов лить - <b>{usr.amount_to_accept}₽</b>\n🔴 Откуда узнал о нас - <i>{usr.info}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="✅ Принять",
                        callback_data=f"accept_true_{usr.telegram_chat_id}",
                    )],
                    [InlineKeyboardButton(
                        text="⛔️ Отклонить",
                        callback_data=f"accept_false_{usr.telegram_chat_id}",
                    )],
                ])
            )

            await message.pin()

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Ваша заявка принята и отправлена на рассмотрение администратору. Ожидайте.",
                parse_mode="HTML",
            )

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"💔 Возникла ошибка, попробуйте позже.\n\n<i>{e}</i>",
                parse_mode="HTML",
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
        user_to_apply = Processor.objects.filter(telegram_chat_id=user_id)      
        if status == "true":

            try:
                user_to_apply.update(
                    verified_usr=True
                )

                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"✅ Вы приняли пользователя <b>{user_to_apply.first().username}</b>.\n\n💰 Теперь укажите комиссию, которую мы даем <b>{user_to_apply.first().username}</b>.",
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
            user = Processor.objects.get(pk=int(context.user_data["user_id_applied"]))
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
                0: [CallbackQueryHandler(self._ask_about_income_avaliable, "start_questions")],
                1: [CallbackQueryHandler(self._ask_where_are_you_from, "^ready_to_accept_")],
                2: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._save_user_apply_and_send_to_admin)]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=500
        ))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._new_user_acception, "^accept_")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._set_comission)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))