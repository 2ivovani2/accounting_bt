from ..applier_bot import ApplierBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChequeWork(ApplierBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
        
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
            f"💵 Отправьте сумму чека(ов)",
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
    async def _ask_for_photo(update: Update, context: CallbackContext) -> None:
        """Функция прошения фото чека

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        usr, _ = await user_get_by_update(update)
        
        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        try:
            context.user_data["cheque_amount"] = int(update.message.text.strip())
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"📷 Отправьте фото чека(ов).\n\n<blockquote>Если вы хотите, отправить более 1 чека, то вам необходимо отправлять все чеки одним сообщением, иначе будет обработан только первый чек.</blockquote>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 Назад",
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
                            text="💎 В меню",
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
                f"🤩 Новая оплата от <b>{usr.username}</b> на сумму <b>{amt}</b> рублей.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Принять оплату чека ✅",
                        callback_data=f"acception_cheque_true_{new_cheque.cheque_id}",
                    )], 
                    [InlineKeyboardButton(
                        text="Пошел он нахуй ⛔️",
                        callback_data=f"acception_cheque_false_{new_cheque.cheque_id}",
                    )]
                ])
            )

            await cont.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Ваш чек(и) были успешно отправлены.\n\n<blockquote>Если хотите повторить операцию, нажмите на соответствующую кнопку</blockquote>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔄 Отправить еще",
                        callback_data=f"send_cheque",
                    )], 
                    [InlineKeyboardButton(
                        text="🔙 В меню",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )
            for index, msg in enumerate(msgs):
                cont.bot_data["messages"][
                    cont.job.data[index]["post_id"]
                ] = msg.message_id
            
            return ConversationHandler.END
        
        try:
            amt = int(context.user_data.get('cheque_amount'))
            new_cheque = Cheque(
                cheque_id=f"#{secrets.token_urlsafe(int(os.environ.get('IDS_LEN'))).replace('_', '')}",
                cheque_sum=amt,
                cheque_owner=usr,
                income=(amt * usr.comission * 0.01)
            )
            new_cheque.save()

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"⛔️ Во время отправки чека возникла ошибка:\n\n<pre>{e}</pre> ",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 В меню",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )

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
                        callback_data=f"acception_cheque_true_{new_cheque.cheque_id}",
                    )], 
                    [InlineKeyboardButton(
                        text="Пошел он нахуй ⛔️",
                        callback_data=f"acception_cheque_false_{new_cheque.cheque_id}",
                    )]
                ])
            )

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Ваш чек были успешно отправлены.\n\n<blockquote>Если хотите повторить операцию, нажмите на соответствующую кнопку</blockquote>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔄 Отправить еще",
                        callback_data=f"send_cheque",
                    )], 
                    [InlineKeyboardButton(
                        text="🔙 В меню",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )
            context.bot_data["messages"][message.message_id] = message.message_id 

    @check_user_status
    async def _new_cheque_acception(update: Update, context: CallbackContext) -> None:
        """Функция подтверждения/отмены принятия xtrf

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        
        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        # try:
        new_cheque = Cheque.objects.filter(cheque_id=query.data.split("_")[-1]).first()
        amount, status = new_cheque.cheque_sum, query.data.split("_")[-2]

        user_to_update = new_cheque.cheque_owner

        if status == "true":
            new_cheque.is_applied = True
            user_to_update.balance += int(amount) - (int(amount) * user_to_update.comission * 0.01)
            user_to_update.save()

            if Ref.objects.filter(whom_invited=user_to_update).exists():
                ref_relation = Ref.objects.filter(whom_invited=user_to_update).first()
                ref_relation.ref_income += int(amount) * 0.01 * int(os.environ.get("REF_PERCENT", 1))
                ref_relation.save()

                who_invited = ref_relation.who_invited
                who_invited.balance += int(amount) * 0.01 * int(os.environ.get("REF_PERCENT", 1))
                who_invited.save()

                await context.bot.send_message(
                    who_invited.telegram_chat_id,
                    f"💰 <i>НОВОЕ ПОСТУПЛЕНИЕ</i> 💰\n\n<blockquote>• Ваш реферал - <b>{user_to_update.username}</b>\n• Сумма чека - <b>{new_cheque.cheque_sum}</b>\n• Ваша прибыль - <b>{int(int(new_cheque.cheque_sum) * 0.01 * int(os.environ.get('REF_PERCENT', 1)))}₽</b></blockquote>\n\nСумма уже зачислена на ваш баланс.",
                    parse_mode="HTML",
                )


            gc = gspread.service_account(filename=os.environ.get("GOOGLE_CREDS"))
            table = gc.open(os.environ.get("TABLE_NAME")).sheet1

            def table_update(date, value, user_name):
                length = len(table.col_values(1)) + 1

                table.update_cell(length, 1, date)
                table.update_cell(length, 2, int(value))
                table.update_cell(length, 3, user_name)

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🪛 Вы приняли чек <b>{new_cheque.cheque_id}</b> от <b>{new_cheque.cheque_owner.username}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}</b>.",
                parse_mode="HTML",
            )

            await context.bot.send_message(
                user_to_update.telegram_chat_id,
                f"✅ Чек <b>{new_cheque.cheque_id}</b> принят!\n• Сумма чека - <b>{new_cheque.cheque_sum}₽</b>\n• Дата чека - <b>{str(new_cheque.cheque_date).split('.')[:1][0]}(МСК)</b>\n• Ваша доля - <b>{new_cheque.cheque_sum - new_cheque.income}₽</b>\n• Текущий баланс - <b>{user_to_update.balance}₽</b>",
                parse_mode="HTML",
                reply_markup = None
            )

            try:
                table_update(str(new_cheque.cheque_date), new_cheque.cheque_sum, str(new_cheque.cheque_owner.username))
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"📄 Google Таблицы успешно обновлены. Чек добавлен.",
                    parse_mode="HTML",
                )
            except Exception as e:
                logging.info(f"Error in google table update - {e}")

        else:
            new_cheque.is_denied = True
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"⚔️ Вы отклонили чек <b>{new_cheque.cheque_id}</b> от <b>{new_cheque.cheque_owner.username}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}</b>.",
                parse_mode="HTML",
            )

            await context.bot.send_message(
                user_to_update.telegram_chat_id,
                f"📛К сожалению, ваш чек <b>{new_cheque.cheque_id}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}(МСК)</b> был отклонен.",
                parse_mode="HTML",
                reply_markup = None
            )

        new_cheque.save()
        
        # except Exception as e:
        #     await context.bot.send_message(
        #         usr.telegram_chat_id,
        #         f"💣 Возникла ошибка.\n\nОшибка: <i>{e}</i>",
        #         parse_mode="HTML",
        #     )

    def reg_handlers(self):
        self.application.add_handler(CallbackQueryHandler(self._new_cheque_acception, "^acception_cheque_"))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_cheque_amount, "send_cheque")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._ask_for_photo)],
                1: [MessageHandler(filters.PHOTO, self._send_photo_to_admin)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start), CallbackQueryHandler(self._ask_for_cheque_amount, "send_cheque")],
            conversation_timeout=300
        ))
