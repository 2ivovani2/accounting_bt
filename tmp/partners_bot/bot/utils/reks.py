from ..processors_bot import ProcessorsBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class ReksModule(ProcessorsBot):
    """Модуль для управления реквизитами пользователей."""

    def __init__(self, app: Application) -> None:
        """Инициализация модуля ReksModule.

        Args:
            app (Application): Экземпляр приложения Telegram.
        """
        super().__init__()
        self.application: Application = app

    @check_user_status
    async def _reks_menu(update: Update, context: CallbackContext) -> None:
        """Обработчик меню управления реквизитами.

        Args:
            update (Update): Объект обновления Telegram.
            context (CallbackContext): Контекст обратного вызова.
        """
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

        usr, _ = await user_get_by_update(update)
        actual_reks = Reks.objects.filter(reks_owner=usr, is_archived=False).all()

        if not actual_reks:
            msg = "😔 Вы пока что не добавили ни одних реквизитов."
        else:
            msg = "🫵 Ваши актуальные реквизиты:\n"
            for r in actual_reks:
                msg += (
                    f"<pre>{r.card_number} / {r.sbp_phone_number} / "
                    f"{r.card_owner_name} / {r.bank_name}</pre>\n\n"
                )

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🚀 Добро пожаловать в меню управления реквизитами.\n\n{msg}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="🍀 Добавить реквизиты",
                    callback_data="add_reks",
                )],
                [InlineKeyboardButton(
                    text="👿 Удалить реквизиты",
                    callback_data="delete_reks",
                )],
                [InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="menu",
                )]
            ])
        )

    @check_user_status
    async def _ask_user_about_reks(update: Update, context: CallbackContext) -> int:
        """Запросить у пользователя ввод реквизитов.

        Args:
            update (Update): Объект обновления Telegram.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: Состояние диалога, ожидающее ввода реквизитов.
        """
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

        usr, _ = await user_get_by_update(update)
        message = (
            "💸 <b>Введите реквизиты в формате</b> ⬇️\n"
            "Номер карты / Номер телефона для перевода по СБП / "
            "ФИО владельца карты / Название банка\n\n"
            "<b>Пример:</b> 2200 1529 4228 9334 / 7-917-598-05-79 / "
            "ИВАНОВ ИВАН ИВАНОВИЧ / Сбер\n\n"
            "<blockquote>‼️ Обратите внимание, что необходимо соблюсти порядок ввода, "
            "как в примере и <b>обязательно</b> разделять каждый пункт слешом - /</blockquote>\n"
            "<blockquote>В случае поступления денег на неверные реквизиты, сумма будет "
            "вычтена из вашего страхового депозита.</blockquote>"
        )
        await context.bot.send_message(
            usr.telegram_chat_id,
            message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="menu",
                )]
            ])
        )
        return 0

    @check_user_status
    async def _reks_prepare_and_setting_to_user(
         update: Update, context: CallbackContext
    ) -> int:
        """Обработчик ввода реквизитов пользователем и сохранение их в систему.

        Args:
            update (Update): Объект обновления Telegram.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: ConversationHandler.END для завершения диалога.
        """
        usr, _ = await user_get_by_update(update)
        reks_input = update.message.text.strip()

        reks_list = [x.strip() for x in reks_input.split("/")]
        if len(reks_list) != 4:
            message = (
                "😡 Введенные вами данные не соответствуют формату. "
                "Внимательно изучите формат отправки реквизитов и попробуйте еще раз."
            )
            await context.bot.send_message(
                usr.telegram_chat_id,
                message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="menu",
                    )]
                ])
            )
            return ConversationHandler.END
        else:
            card_number, phone_number, name, bank_name = reks_list
            if len(card_number.replace(" ", "")) != 16:
                message = (
                    "👺 Введенные вами данные карты некорректны. "
                    "Проверьте и попробуйте еще раз."
                )
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="menu",
                        )]
                    ])
                )
                return ConversationHandler.END

            elif Reks.objects.filter(card_number=card_number).exists():
                message = "🙁 Вы уже добавляли эти реквизиты, попробуйте другие."
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="menu",
                        )]
                    ])
                )
                return ConversationHandler.END

            else:
                card_number = re.sub(r"(\d{4})(?=\d)", r"\1 ", card_number)

            clean_number = re.sub(r"[ \-\(\)]", "", phone_number)
            pattern = r"^(\+7|7|8)(\d{10})$"
            match = re.match(pattern, clean_number)

            if match:
                formatted_number = "+7 ({}) {}-{}-{}".format(
                    match.group(2)[:3],
                    match.group(2)[3:6],
                    match.group(2)[6:8],
                    match.group(2)[8:]
                )
                phone_number = formatted_number
            else:
                message = (
                    "💀 Введенный вами номер телефона некорректен. "
                    "Проверьте и попробуйте еще раз."
                )
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="menu",
                        )]
                    ])
                )
                return ConversationHandler.END

            try:
                rek = Reks.objects.create(
                    reks_owner=usr,
                    card_number=card_number,
                    sbp_phone_number=phone_number,
                    card_owner_name=name.upper(),
                    bank_name=bank_name.upper()
                )

                message = (
                    "✅ Новые реквизиты успешно добавлены.\n\n"
                    f"<pre>{rek.card_number} / {rek.sbp_phone_number} / "
                    f"{rek.card_owner_name} / {rek.bank_name}</pre>"
                )
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="menu",
                        )],
                    ])
                )

            except Exception as e:
                message = f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>"
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 В начало",
                            callback_data="menu",
                        )],
                    ])
                )

        return ConversationHandler.END

    @check_user_status
    async def _ask_user_card_number_to_delete_reks(
        update: Update, context: CallbackContext
    ) -> int:
        """Запрос номера карты для удаления реквизитов.

        Args:
            update (Update): Объект обновления Telegram.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: Состояние диалога, ожидающее ввода номера карты.
        """
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

        usr, _ = await user_get_by_update(update)
        message = (
            "🤔 Введите номер карты реквизитов, которые хотите удалить в формате ⤵️\n"
            "<pre>1111 2222 3333 4444</pre>"
        )
        await context.bot.send_message(
            usr.telegram_chat_id,
            message,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="menu",
                )],
            ])
        )

        return 0

    @check_user_status
    async def _delete_user_reks(update: Update, context: CallbackContext) -> int:
        """Удаление реквизитов пользователя по номеру карты.

        Args:
            update (Update): Объект обновления Telegram.
            context (CallbackContext): Контекст обратного вызова.

        Returns:
            int: ConversationHandler.END для завершения диалога.
        """
        usr, _ = await user_get_by_update(update)
        card_number_input = update.message.text.strip().replace(" ", "")

        if len(card_number_input) == 16:
            card_number = re.sub(r"(\d{4})(?=\d)", r"\1 ", card_number_input)
            rek = Reks.objects.filter(
                card_number=card_number,
                reks_owner=usr,
                is_archived=False
            ).first()
            if rek:
                rek.is_archived = True
                rek.save()

                message = (
                    "✅ Вы успешно удалили реквизиты:\n\n"
                    f"<pre>{rek.card_number} / {rek.sbp_phone_number} / "
                    f"{rek.card_owner_name} / {rek.bank_name}</pre>"
                )
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="menu",
                        )],
                    ])
                )
            else:
                message = (
                    "🙉 Таких реквизитов, которые вы отправили либо не существует, "
                    "либо вы их уже удалили."
                )
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    message,
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="menu",
                        )],
                    ])
                )
        else:
            message = (
                "🌪️ Неверное количество символов в номере карты, обратите внимание "
                "на пример формата ⤵️\n<pre>1111 2222 3333 4444</pre>"
            )
            await context.bot.send_message(
                usr.telegram_chat_id,
                message,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="menu",
                    )],
                ])
            )

        return ConversationHandler.END

    def reg_handlers(self) -> None:
        """Регистрация обработчиков команд и состояний."""
        self.application.add_handler(ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self._ask_user_card_number_to_delete_reks, pattern="delete_reks"
                )
            ],
            states={
                0: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self._delete_user_reks
                    )
                ],
            },
            fallbacks=[
                CallbackQueryHandler(self._start, pattern="menu"),
                CommandHandler("start", self._start)
            ],
            conversation_timeout=300
        ))

        self.application.add_handler(ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self._ask_user_about_reks, pattern="add_reks"
                )
            ],
            states={
                0: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self._reks_prepare_and_setting_to_user
                    )
                ],
            },
            fallbacks=[
                CallbackQueryHandler(self._start, pattern="menu"),
                CommandHandler("start", self._start)
            ],
            conversation_timeout=600
        ))

        self.application.add_handler(
            CallbackQueryHandler(self._reks_menu, pattern="reks_profile")
        )