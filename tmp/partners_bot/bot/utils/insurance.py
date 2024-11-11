from ..processors_bot import ProcessorsBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class Insurance(ProcessorsBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
    
    async def _info_user_about_deposit(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

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
        if usr.has_active_paying_insurance_apply:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"‼️ Уважаемый <b>{usr.username}</b>, у вас уже есть активная заявка на оплату страхового депозита.<blockquote>Пожалуйста, ожидайте, администраторы рассмотрят вашу заявку в порядке очереди в ближайшее время.</blockquote>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="menu",
                    )]
                ])
            )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🥶 Уважаемый <b>{usr.username}</b>, для активации профиля, необходимо внести страховой депозит.\n\nМинимальная сумма депозита - <b>10.000₽</b>.\n\n<blockquote>‼️ Обратите внимание, вы не сможете заливаться больше страхового депозита, пока не выведите фиатный баланс.\n\nДля удобной работы, советуем внести сумму выше, чтобы не делать более <b>1-3</b> выводов в день.\n\nКурс устанавливается по 1-2 предложению в ByBit, раздел SBP/SBER/RAIFFEISEN💸</blockquote>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="💸 Внести",
                        callback_data="pay_insurance_info",
                    )],
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="menu",
                    )]
                ])
            )
            
            return 0
        return ConversationHandler.END

    async def _give_user_reks_to_pay_insurance(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

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
        
        try:
            deposit = InsurancePayment(
                owner=usr,
                payment_sum_rub=round(usr.amount_to_accept * 1.1, 2),
                payment_sum_usdt=round(usr.amount_to_accept * 1.1 / context.bot_data["usdt_price"], 2),
            )
            deposit.save()

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"Внесите страховой депозит удобным для вас способом⤵️\n\nСумма к оплате - <b>{deposit.payment_sum_rub}₽ / {deposit.payment_sum_usdt}USDT</b>\n\nUSDT TRC20 - <pre>{os.environ.get('ACCEPT_INSURANCE_PAYMENTS_ADDRESS')}</pre>\n\n<b>RUB/UAH/KZT</b> - @{os.environ.get('PROCESSORS_ADMIN_USERNAME')}",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="✅ Оплатил",
                        callback_data=f"user_paid_{deposit.id}",
                    )],
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="menu",
                    )]
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

        return 1

    async def _send_insurance_apply_to_admin(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

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
        admin = Processor.objects.filter(username=os.environ.get("PROCESSORS_ADMIN_USERNAME")).first()
        deposit_id = query.data.split("_")[-1]
        deposit = InsurancePayment.objects.get(pk=deposit_id)    

        try:
            usr.has_active_paying_insurance_apply = True
            usr.save()

            msg = await context.bot.send_message(
                admin.telegram_chat_id,
                f"⭐️ Новая заявка на оплату страхового депозита от <b>{deposit.owner.username}</b>:\n\n· Сумма - <b>{deposit.payment_sum_rub}₽ / {deposit.payment_sum_usdt}USDT</b>\n· Курс - <b>{context.bot_data['usdt_price']}</b>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="✅ Подтвердить",
                        callback_data=f"insurance_payment_accept_{deposit_id}",
                    )],
                    [InlineKeyboardButton(
                        text="⛔️ Отклонить",
                        callback_data=f"insurance_payment_decline_{deposit_id}",
                    )], 
                ])
            )

            await msg.pin()

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"✅ Заявка успешно создана.\n\n<blockquote>Ожидайте подтверждения админимьтратора, обычно это занимает от 3-6 часов.</blockquote>",
                parse_mode="HTML",                    
            )

        except Exception as e:
            usr.has_active_paying_insurance_apply = False
            usr.save()

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

    async def _apply_insurance_by_admin(self, update: Update, context: CallbackContext) -> int:
        """
            Обработчик команды /start

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

        admin, _ = await user_get_by_update(update)
        splitted_data = query.data.split("_")
        deposit_id, status = splitted_data[-1], splitted_data[-2]
        deposit = InsurancePayment.objects.get(pk=deposit_id)
        usr = deposit.owner  

        if status == "accept":
            try:
                usr.insurance_deposit = round(usr.amount_to_accept / 1.10, 2)
                usr.is_ready_to_get_money = True
                usr.has_active_paying_insurance_apply = False

                deposit.is_applied = True
                
                usr.save()
                deposit.save()

                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"✅ Вы успешно приняли страховой депозит пользователя <b>{usr.username}</b> на сумму <b>{deposit.payment_sum_rub}₽ / {deposit.payment_sum_usdt}USDT</b>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 В меню",
                            callback_data=f"menu",
                        )], 
                    ])
                )

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"✅ Ваш страховой депозит на сумму <b>{deposit.payment_sum_rub}₽ / {deposit.payment_sum_usdt}USDT</b> успешно принят.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 В меню",
                            callback_data=f"menu",
                        )], 
                    ])
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

        else:
            try:
                usr.has_active_paying_insurance_apply = False
                usr.save()

                await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"⛔️ Вы успешно отклонили страховой депозит пользователя <b>{usr.username}</b> на сумму {deposit.payment_sum_rub}₽ / {deposit.payment_sum_usdt}USDT.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 В меню",
                            callback_data=f"menu",
                        )], 
                    ])
                )

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"⛔️ Ваш страховой депозит на сумму {deposit.payment_sum_rub}₽ / {deposit.payment_sum_usdt}USDT отклонен.\n\n<blockquote>Если вы считаете, что произошла ошибка, свяжитесь с администратором по кнопке ниже.</blockquote>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🆘 Администратор",
                            url=f"https://t.me/{os.environ.get('PROCESSORS_ADMIN_USERNAME')}",
                        )], 
                        [InlineKeyboardButton(
                            text="🔙 В меню",
                            callback_data=f"menu",
                        )], 
                    ])
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

    def reg_handlers(self):
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._info_user_about_deposit, "insurance_deposit")],
            states={
                0: [CallbackQueryHandler(self._give_user_reks_to_pay_insurance, "pay_insurance_info")],
                1: [CallbackQueryHandler(self._send_insurance_apply_to_admin, "^user_paid_")],
                
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=600
        ))

        self.application.add_handler(CallbackQueryHandler(self._apply_insurance_by_admin, "^insurance_payment_"))
