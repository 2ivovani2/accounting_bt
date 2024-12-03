from ..processors_bot import ProcessorsBot
from .imports import *
from .helpers import *
from applier.models import *
from django.conf import settings
from applier.tasks import initialize_bot

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChequeWork(ProcessorsBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
    
    @staticmethod
    async def get_client_bot_instance():
        if settings.CLIENT_BOT_INSTANCE is None:
            await initialize_bot()
        return settings.CLIENT_BOT_INSTANCE

    async def _send_insurance_acception(self, update: Update, context: CallbackContext) -> None:
        """Функция подтверждения/отмены принятия xtrf

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        client_bot = await ChequeWork.get_client_bot_instance()
        admin = Processor.objects.filter(username=os.environ.get("PROCESSORS_ADMIN_USERNAME")).first()

        try:
            query = update.callback_query
            if query:
                await query.answer()
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
                usdt_sum, user_who_send = query.data.split("_")[-1], Processor.objects.filter(telegram_chat_id=int(query.data.split("_")[-2])).first()
        except:
            pass

        await context.bot.send_message(
            admin.telegram_chat_id,
            f"💬 Вам поступила новая оплата для продления работы на сумму <b>{usdt_sum}USDT</b> от <b>{user_who_send.username}</b>.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"working_accept_{user_who_send.telegram_chat_id}",
                )],
                [InlineKeyboardButton(
                    text="⛔️ Отклонить",
                    callback_data=f"working_decline_{user_who_send.telegram_chat_id}",
                )],
            ])
        )

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"✅ Ваша заявка на продление работы успешно отправлена администратору.",
            parse_mode="HTML",
            reply_markup=None
        )

    @check_user_status
    async def _apply_insurance_appliment_by_admin(update: Update, context: CallbackContext) -> None:
        """Функция подтверждения/отмены принятия xtrf

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        admin, _ = await user_get_by_update(update)
        client_bot = await ChequeWork.get_client_bot_instance()
        
        try:
            query = update.callback_query
            if query:
                await query.answer()
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
                status, user_who_wants_to_work = query.data.split("_")[-2], Processor.objects.filter(telegram_chat_id=int(query.data.split("_")[-1])).first()
        except:
            pass
        
        if status == "accept":
            user_who_wants_to_work.is_ready_to_get_money = True
            user_who_wants_to_work.insurance_deposit = round(user_who_wants_to_work.amount_to_accept / 1.10, 2)
            user_who_wants_to_work.save()

            await context.bot.send_message(
                user_who_wants_to_work.telegram_chat_id,
                f"🚀 Ваша выплата принята, можете продолжать работу дальше.",
                parse_mode="HTML",
                reply_markup=None
            )

            await context.bot.send_message(
                admin.telegram_chat_id,
                f"✅ Вы успешно подтвердили платеж от <b>{user_who_wants_to_work.username}</b>\n\n<blockquote><b>ВАЖНО!!</b> Не забудьте установить реквизиты клиенту через админ панель.</blockquote>",
                parse_mode="HTML",
                reply_markup=None
            )

        else:
            await context.bot.send_message(
                user_who_wants_to_work.telegram_chat_id,
                f"😢 Ваша выплата отклонена, обратитесь к администратору для решения вопроса.",
                parse_mode="HTML",
                reply_markup=None
            )

            await context.bot.send_message(
                admin.telegram_chat_id,
                f"⛔️ Вы успешно отклонили платеж от <b>{user_who_wants_to_work.username}</b>\n\n<blockquote><b>ВАЖНО!!</b> Не забудьте установить реквизиты клиенту через админ панель.</blockquote>",
                parse_mode="HTML",
                reply_markup=None
            )
        

    @check_user_status
    async def _new_cheque_acception(update: Update, context: CallbackContext) -> None:
        """Функция подтверждения/отмены принятия xtrf

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        client_bot = await ChequeWork.get_client_bot_instance()

        try:
            query = update.callback_query
            if query:
                await query.answer()
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        except:
            pass

        try:
            new_cheque = Cheque.objects.filter(cheque_id=query.data.split("_")[-1]).first()
            
            if not new_cheque.is_applied and not new_cheque.is_denied:
                amount, status = new_cheque.cheque_sum, query.data.split("_")[-2]
                user_to_update = new_cheque.cheque_owner

                if status == "true":
                    usr.insurance_deposit -= new_cheque.cheque_sum    
                    usr.save()

                    if usr.insurance_deposit <= 0:
                        user_to_update.reks = None
                        user_to_update.save()

                        usr.is_ready_to_get_money = False
                        usr.save()

                        await client_bot.send_message(
                            user_to_update.telegram_chat_id,
                            f"🆘 Ваши реквизиты были изменены, проверьте в разделе <b>Реквизитов</b>.\n\n<blockquote>Если их там не появилось, то обратитесь к администратору.</blockquote>",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup([
                                [
                                    InlineKeyboardButton(
                                        text="💸 Реквизиты", 
                                        callback_data="reks"
                                    ),
                                ],
                            ])
                        )
                        
                        await context.bot.send_message(
                            usr.telegram_chat_id,
                            f"😔 Ваш лимит на принятие чеков закончился, вам необходимо вывести <b>{round((usr.amount_to_accept - usr.insurance_deposit) / context.bot_data.get('usdt_course', 100.0), 2)}USDT</b> на адрес <pre>{os.environ.get('ACCEPT_INSURANCE_PAYMENTS_ADDRESS','TJbfLnybJxXKoPVrdFfSAGkEoAr1g4DmpW')}</pre>\n\n<blockquote>Если вы не оплатите сумму, тогда мы будем вынуждены забрать себе страховой депозит и прекратить с вами работу.</blockquote>",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton(
                                    text="🔙 Назад",
                                    callback_data="menu",
                                )],
                                [InlineKeyboardButton(
                                    text="🌪️ Я оплатил",
                                    callback_data=f"reset_insurance_apply_{usr.telegram_chat_id}_{round((usr.amount_to_accept - usr.insurance_deposit) / context.bot_data.get('usdt_course', 100.0), 2)}",
                                )],
                            ])
                        )
                    
                    
                    new_cheque.is_applied = True
                    user_to_update.balance = round(float(user_to_update.balance), 2) + round(float(amount) - (float(amount) * user_to_update.comission * 0.01), 2)
                    user_to_update.save()

                    usr.balance = round(float(usr.balance), 2) + new_cheque.cheque_sum * usr.comission * 0.01
                    usr.save()

                    if Ref.objects.filter(whom_invited=user_to_update).exists():
                        ref_relation = Ref.objects.filter(whom_invited=user_to_update).first()
                        ref_relation.ref_income += int(amount) * 0.01 * int(os.environ.get("REF_PERCENT", 1))
                        ref_relation.save()

                        who_invited = ref_relation.who_invited
                        who_invited.balance = round(who_invited.balance, 2) + round(float(amount) * 0.01 * int(os.environ.get("REF_PERCENT", 1)), 2)
                        who_invited.save()

                        await client_bot.send_message(
                            who_invited.telegram_chat_id,
                            f"💰 <i>НОВОЕ ПОСТУПЛЕНИЕ</i> 💰\n\n<blockquote>• Ваш реферал - <b>{user_to_update.username}</b>\n• Сумма чека - <b>{new_cheque.cheque_sum}</b>\n• Ваша прибыль - <b>{int(int(new_cheque.cheque_sum) * 0.01 * int(os.environ.get('REF_PERCENT', 1)))}₽</b></blockquote>\n\nСумма уже зачислена на ваш баланс.",
                            parse_mode="HTML",
                        )

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"🪛 Вы приняли чек <b>{new_cheque.cheque_id}</b> от <b>{new_cheque.cheque_owner.username}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}</b>.",
                        parse_mode="HTML",
                    )

                    await client_bot.send_message(
                        user_to_update.telegram_chat_id,
                        f"✅ Чек <b>{new_cheque.cheque_id}</b> принят!\n• Сумма чека - <b>{new_cheque.cheque_sum}₽</b>\n• Дата чека - <b>{str(new_cheque.cheque_date).split('.')[:1][0]}(МСК)</b>\n• Ваша доля - <b>{new_cheque.cheque_sum - new_cheque.income}₽</b>\n• Текущий баланс - <b>{user_to_update.balance}₽</b>",
                        parse_mode="HTML",
                        reply_markup = None
                    )

                else:
                    new_cheque.is_denied = True
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"⚔️ Вы отклонили чек <b>{new_cheque.cheque_id}</b> от <b>{new_cheque.cheque_owner.username}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}</b>.",
                        parse_mode="HTML",
                    )

                    await client_bot.send_message(
                        user_to_update.telegram_chat_id,
                        f"📛К сожалению, ваш(и) чек(и) <b>{new_cheque.cheque_id}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}(МСК)</b> был отклонен.",
                        parse_mode="HTML",
                        reply_markup = None
                    )

                new_cheque.save()
            
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"⭐️ Данный чек уже был обработан.",
                    parse_mode="HTML",
                )
                
        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"💣 Возникла ошибка.\n\nОшибка: <i>{e}</i>",
                parse_mode="HTML",
            )

    def reg_handlers(self):
        self.application.add_handler(CallbackQueryHandler(self._new_cheque_acception, "^acception_cheque_"))
        self.application.add_handler(CallbackQueryHandler(self._send_insurance_acception, "^reset_insurance_apply_"))
        self.application.add_handler(CallbackQueryHandler(self._apply_insurance_appliment_by_admin, "^working_"))