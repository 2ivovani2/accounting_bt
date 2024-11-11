from ..processors_bot import ProcessorsBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class ReksModule(ProcessorsBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
    
    async def _reks_menu(self, update: Update, context: CallbackContext) -> int:
        """
            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """

        try:
            query = update.callback_query
            if query:
                await query.answer()
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        except:
            pass

        usr, _ = await user_get_by_update(update)
        
        actual_reks = Reks.objects.filter(reks_owner=usr, is_archived=False).all()
        msg = ""
        if len(actual_reks) == 0:
            msg = "😔 Вы пока что не добавили ни одних реквизитов."
        else:
            msg = "🫵 Ваши актуальные реквизиты:\n"
            for r in actual_reks:
                msg += f"<pre>{r.card_number} / {r.sbp_phone_number} / {r.card_owner_name} / {r.bank_name}</pre>\n\n"

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🚀 Добро пожаловать в меню управления реквизитами.\n\n{msg}",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
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

    async def _ask_user_about_reks(self, update: Update, context: CallbackContext) -> int:
        """
            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """

        try:
            query = update.callback_query
            if query:
                await query.answer()
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        except:
            pass

        usr, _ = await user_get_by_update(update)
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"💸 <b>Введите реквизиты в формате</b> ⬇️\nНомер карты / Номер телефона для перевода по СБП / ФИО владельца карты/ Название банка\n\n<b>Пример:</b> 2200 1529 4228 9334 / 7-917-598-05-79 / ИВАНОВ ИВАН ИВАНОВИЧ / Сбер\n\n<blockquote>‼️ Обратите внимание, что необходимо соблюсти порядок ввода, как в примере и <b>обязательно</b> разделять каждый пункт слешом - /</blockquote>\n<blockquote>В случае поступления денег на неверные реквизиты, сумма будет вычтена из вашего страхового депозита.</blockquote>",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="reks_profile",
                )]
            ])
        )
        return 0
        
    async def _reks_prepare_and_setting_to_user(self, update: Update, context: CallbackContext) -> int:
        """
            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """
        usr, _ = await user_get_by_update(update)
        reks = update.message.text.strip()

        reks = list(map(lambda x: x.strip(), reks.split("/")))
        if len(reks) != 4:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"😡 Введенные вами данные не соотвествую формату. Внимательно изучите формат отправки реквизитов и пропробуйте еще раз.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="reks_profile",
                    )]
                ])
            )
            return ConversationHandler.END
        else:
            card_number, phone_number, name, bank_name = reks
            if len(card_number.replace(" ", "")) != 16:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"👺 Введенные вами данные карты некорректны. Проверьте и пропробуйте еще раз.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="reks_profile",
                        )]
                    ])
                )
                return ConversationHandler.END
            
            elif Reks.objects.filter(card_number=card_number).exists():
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🙁 Вы уже добавляли эти реквизиты, попробуйте другие.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="reks_profile",
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
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"💀 Введенный вами номер телефона некорректен. Проверьте и пропробуйте еще раз.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="reks_profile",
                        )]
                    ])
                )
                return ConversationHandler.END

            try:
                rek = Reks(
                    reks_owner=usr,
                    card_number=card_number,
                    sbp_phone_number=phone_number,
                    card_owner_name=name.upper(),
                    bank_name=bank_name.upper()
                )
                rek.save()

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"✅ Новые реквизиты успешно добавлены.\n\n<pre>{rek.card_number} / {rek.sbp_phone_number} / {rek.card_owner_name} / {rek.bank_name}</pre>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data=f"reks_profile",
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
                            text="🔙 В начало",
                            callback_data=f"menu",
                        )], 
                    ])
                )

        return ConversationHandler.END
    
    def reg_handlers(self):
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_user_about_reks, "add_reks")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._reks_prepare_and_setting_to_user)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CallbackQueryHandler(self._reks_menu, "reks_profile"),CommandHandler("start", self._start)],
            conversation_timeout=600
        ))

        self.application.add_handler(CallbackQueryHandler(self._reks_menu, "reks_profile"))
