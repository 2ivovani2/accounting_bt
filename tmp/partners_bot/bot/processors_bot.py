from .utils.imports import *
from .utils.helpers import *

class ProcessorsBot:
    """Класс для управления ботом ProcessorsBot."""

    def __init__(self) -> None:
        """Инициализация приложения бота."""
        self.application: Application = (
            ApplicationBuilder()
            .token(os.environ.get('PROCESSORS_BOT_TOKEN'))
            .build()
        )

    async def _start(self, update: Update, context: CallbackContext) -> int:
        """Обработчик команды /start.

        Args:
            update (Update): Объект обновления.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: Завершает диалог, возвращая ConversationHandler.END.
        """
        usr, created = await user_get_by_update(update)

        try:
            query = update.callback_query
            if query:
                await query.answer()
                await context.bot.delete_message(
                    chat_id=query.message.chat_id,
                    message_id=query.message.message_id
                )
        except Exception:
            pass

        if not usr.verified_usr:
            message = (
                f"🤩 <b>{usr.username}</b>, добрый день, если хотите отправить "
                "заявку на прием платежей, нажмите кнопку ниже."
            )
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="🤘🏻 Отправить заявку",
                    callback_data="create_apply",
                )]
            ])
            await context.bot.send_message(
                usr.telegram_chat_id,
                message,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        else:
            if not usr.is_superuser:
                if "usdt_price" in context.bot_data:
                    course = context.bot_data["usdt_price"]
                else:
                    try:
                        url = "https://api.binance.com/api/v3/ticker/price"
                        params = {"symbol": "USDTRUB"}
                        response = requests.get(url, params=params)
                        ticker_info = response.json()

                        if 'price' in ticker_info:
                            course = (
                                round(float(ticker_info['price']), 2)
                                + float(os.environ.get("NADBAVKA", 0))
                            )
                            context.bot_data["usdt_price"] = course
                        else:
                            message = (
                                "⛔️ Возникла ошибка во время получения цены "
                                "<b>USDT/RUB</b>.\n\n"
                                "Если проблема повторяется, обратитесь к администратору."
                            )
                            reply_markup = InlineKeyboardMarkup([
                                [InlineKeyboardButton(
                                    text="💎 В меню",
                                    callback_data="menu",
                                )],
                                [InlineKeyboardButton(
                                    text="🆘 Администратор",
                                    url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                                )],
                            ])
                            await context.bot.send_message(
                                usr.telegram_chat_id,
                                message,
                                parse_mode="HTML",
                                reply_markup=reply_markup
                            )
                            return ConversationHandler.END
                    except Exception as e:
                        message = (
                            "⛔️ Возникла ошибка во время получения цены "
                            "<b>USDT/RUB</b>.\n\n"
                            f"Ошибка: <i>{e}</i>"
                        )
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎 В меню",
                                callback_data="menu",
                            )],
                            [InlineKeyboardButton(
                                text="🆘 Администратор",
                                url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                            )],
                        ])
                        await context.bot.send_message(
                            usr.telegram_chat_id,
                            message,
                            parse_mode="HTML",
                            reply_markup=reply_markup
                        )
                        return ConversationHandler.END

                message = (
                    f"<b>Ⓘ <u>ID профиля</u></b> - {usr.telegram_chat_id}\n\n"
                    f"· Статус аккаунта: "
                    f"{'<b>Активен ✅</b>' if usr.is_ready_to_get_money else '<b>Не активен 📛</b>'}\n\n"
                    f"· Текущий баланс: <b>{usr.balance}₽</b>\n"
                    f"· Текущая комиссия: <b>{usr.comission}%</b>\n"
                    f"· Курс USDT/RUB: <b>{course}₽</b>\n\n"
                    f"<b>Возникли тех неполадки ⤵️</b> "
                    f"@{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                )
                reply_markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            text="💬 FAQ",
                            url=os.environ.get("FAQ_LINK")
                        ),
                        InlineKeyboardButton(
                            text="⭐️ Вывод",
                            callback_data="get_withdraw"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="💵 Реквизиты",
                            callback_data="reks_profile"
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            text="💸 Активировать профиль",
                            callback_data="insurance_deposit"
                        ),
                    ] if not usr.is_ready_to_get_money_first else [],
                ])
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )
            else:
                message = f"🤩 <b>{usr.username}</b>, приветик!"
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Установить курс 💲",
                        callback_data="set_course",
                    )],
                    [InlineKeyboardButton(
                        text="Админка 👀",
                        web_app=WebAppInfo(url=f"{os.environ.get('DOMAIN_NAME')}/admin")
                    )]
                ])
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=reply_markup
                )

        return ConversationHandler.END

    @check_user_status
    async def _ask_about_partner_withdraw(
        update: Update, context: CallbackContext
    ) -> int:
        """Запросить курс у администратора.

        Args:
            update (Update): Объект обновления.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: Состояние диалога, ожидающий ввод курса.
        """
        usr, _ = await user_get_by_update(update)
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🍀 Выводы в данный момент происходят в ручном режиме, если вам необходим вывод, то обратитесь к администратору.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В начало 🔰",
                    callback_data="menu",
                )],
            ])
        )


    @check_user_status
    async def _ask_for_course_from_admin(
        update: Update, context: CallbackContext
    ) -> int:
        """Запросить курс у администратора.

        Args:
            update (Update): Объект обновления.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: Состояние диалога, ожидающий ввод курса.
        """
        usr, _ = await user_get_by_update(update)
        message = "😀 Введите курс, который установим."
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text="В начало 🔰",
                callback_data="menu",
            )],
        ])
        await context.bot.send_message(
            usr.telegram_chat_id,
            message,
            parse_mode="HTML",
            reply_markup=reply_markup
        )

        return 0

    @check_user_status
    async def _set_course(
        update: Update, context: CallbackContext
    ) -> int:
        """Установить курс, введенный администратором.

        Args:
            update (Update): Объект обновления.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: ConversationHandler.END для завершения диалога.
        """
        usr, _ = await user_get_by_update(update)
        try:
            course = round(float(update.message.text.strip()), 2)
            context.bot_data["usdt_price"] = course

            message = f"🤩 Вы успешно установили курс <b>{course}</b>"
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В начало 🔰",
                    callback_data="menu",
                )],
            ])
            await context.bot.send_message(
                usr.telegram_chat_id,
                message,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        except Exception as e:
            message = f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>"
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В начало 🔰",
                    callback_data="menu",
                )],
            ])
            await context.bot.send_message(
                usr.telegram_chat_id,
                message,
                parse_mode="HTML",
                reply_markup=reply_markup
            )

        return ConversationHandler.END

    def register_handlers(self) -> Application:
        """Регистрация обработчиков в приложении.

        Returns:
            Application: Приложение с зарегистрированными обработчиками.
        """
        self.application.add_handler(ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self._ask_for_course_from_admin, pattern="set_course"
                )
            ],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._set_course)],
            },
            fallbacks=[
                CallbackQueryHandler(self._start, pattern="menu"),
                CommandHandler("start", self._start)
            ],
            conversation_timeout=300
        ))

        return self.application

    def set_last_handlers(self, application: Application) -> Application:
        """Установка финальных обработчиков в приложении.

        Args:
            application (Application): Экземпляр приложения.

        Returns:
            Application: Приложение с добавленными обработчиками.
        """

        application.add_handler(CommandHandler("start", self._start))
        application.add_handler(CallbackQueryHandler(self._start, pattern="menu"))

        application.add_handler(CallbackQueryHandler(self._ask_about_partner_withdraw, "get_withdraw"))

        from django.conf import settings
        settings.PARTNERS_APPLICATION = application
        settings.PARTNERS_BOT_INSTANCE = application.bot

        return application


