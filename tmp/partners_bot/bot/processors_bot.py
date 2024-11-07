from .utils.imports import *
from .utils.helpers import *


class ProcessorsBot:
    
    def __init__(self) -> None:
        """"
            Инициализация апа
        """
            
        self.application = (
            ApplicationBuilder()
            .token(os.environ.get('PROCESSORS_BOT_TOKEN'))
            .build()
        )

    async def _start(self, update: Update, context: CallbackContext):
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """

        usr, created = await user_get_by_update(update)

        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        if not usr.verified_usr:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 <b>{usr.username}</b>, добрый день, если хотите отправить заявку на прием платежей, нажмите кнопку ниже.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🤘🏻 Отправить заявку",
                        callback_data="create_apply",
                    )]
                ])
            )
        else:
            if not usr.is_superuser:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"Салам бабайчикам",
                    parse_mode="HTML",
                )
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🤩 <b>{usr.username}</b>, приветик!",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Установить курс 💲",
                            callback_data="set_course",
                        )],
                        [InlineKeyboardButton(
                            text="Админка 👀",
                            web_app=WebAppInfo(url=f"{os.environ.get('DOMAIN_NAME')}/admin")
                        )]
                    ])
                )

        return ConversationHandler.END
    
    @check_user_status
    async def _ask_for_course_from_admin(update: Update, context: CallbackContext) -> None:
        """Функция узначи курса

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"😀 Введите курс, который установим.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В начало 🔰",
                    callback_data=f"menu",
                )], 
                
            ])
        )

        return 0

    @check_user_status
    async def _set_course(update: Update, context: CallbackContext) -> None:
        """Функция узначи курса

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        try:
            course = round(float(update.message.text.strip()), 2)
            context.bot_data["usdt_price"] = course
         
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 Вы успешно установили курс <b>{course}</b>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В начало 🔰",
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

        return ConversationHandler.END

    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_course_from_admin, "set_course")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._set_course)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        return self.application

    def set_last_handlers(self, application):
        application.add_handler(CommandHandler("start", self._start))
        application.add_handler(CallbackQueryHandler(self._start, "menu"))

        return application



