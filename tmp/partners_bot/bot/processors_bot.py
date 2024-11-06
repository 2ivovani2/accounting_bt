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
                )

        return ConversationHandler.END
    
    

    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """
        

        return self.application

    def set_last_handlers(self, application):
        application.add_handler(CommandHandler("start", self._start))
        application.add_handler(CallbackQueryHandler(self._start, "menu"))

        return application



