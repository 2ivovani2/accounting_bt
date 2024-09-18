from ..applier_bot import ApplierBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class Metrics(ApplierBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
    
    @check_user_status
    async def _ask_for_username_in_stat(update: Update, context: CallbackContext) -> None:
        """Получения юзернейма

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 Отправьте имя пользователя в формате <b>@username</b> или просто <b>username</b>.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 💎",
                        callback_data="menu",
                    )],
                ])
        )

        return 0

    @check_user_status
    async def _ask_for_stat(update: Update, context: CallbackContext) -> None:
        """Функция для получения статистики

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        username_to_get_stat = update.message.text.strip().replace("@", "")

        if not ApplyUser.objects.filter(username=username_to_get_stat).exists():
            await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"❌ Пользователя с таким юзернемом не существует.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В меню 💎",
                            callback_data="menu",
                        )],
                    ])
                )

            return ConversationHandler.END
        else:
            context.user_data["username_stat"] = update.message.text.strip().replace("@", "")

            if usr.is_superuser:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🪛 Выберите операцию, которая вас интересует.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Стат за день ☀️",
                            callback_data="stat_day",
                        )], 
                        [InlineKeyboardButton(
                            text="Стат за все время ⏳",
                            callback_data="stat_all",
                        )],
                        [InlineKeyboardButton(
                            text="В меню 💎",
                            callback_data="menu",
                        )],
                    ])
                )

                return 1
            
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🆘 К сожалению, у вас недостаточно прав для выполнения данной операции.",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В начало 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )

                return ConversationHandler.END

    @check_user_status
    async def _get_stat(update: Update, context: CallbackContext) -> None:
        """Функция для получения статистики

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        
        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        user_info_about = context.user_data.get("username_stat", None)
        if not user_info_about:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🆘 К сожалению, пользователь не найден, попробуйте еще раз.",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В начало 🔰",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )
            return ConversationHandler.END

        type_of_oper = query.data.split("_")[-1]
        if type_of_oper == "day":

            cheques = Cheque.objects.filter(
                cheque_owner=ApplyUser.objects.filter(username=user_info_about).first(),
                cheque_date__date=timezone.now()
            ).all()

            withdraws = Withdraw.objects.filter(
                withdraw_owner=ApplyUser.objects.filter(username=user_info_about).first(),
                withdraw_date__date=timezone.now()    
            ).all()

            total_cheques_sum, total_withdraw_sum, total_income = 0, 0, 0
            end_msg = f"💰 Статистика о пользователе <b>{ApplyUser.objects.filter(username=user_info_about).first().username}</b> за сегодня:\n\n<b>Чеки:</b>\n"
            
            if len(cheques) == 0:
                end_msg += "🙁 Сегодня чеков не было.\n"
            else:
                for cheque in cheques:
                    if cheque.is_applied:
                        total_cheques_sum += cheque.cheque_sum
                        total_income += cheque.income

                    if not cheque.is_applied and not cheque.is_denied:
                        status = "В работе"
                    elif cheque.is_applied:
                        status = "Принят"
                    else:
                        status = "Не принят"
                
                    end_msg += f"<i>{cheque.cheque_id} - {cheque.cheque_sum}₽ - {status} - {cheque.income}₽</i>\n"
            
            end_msg += "\n<b>Выводы:</b>\n"

            if len(withdraws) == 0:
                end_msg += "🙁 Сегодня выводов не было.\n"
            else:
                for withdraw in withdraws:
                    if withdraw.is_applied:
                        total_withdraw_sum += withdraw.withdraw_sum

                    if not withdraw.is_applied:
                        status = "В работе"
                    elif withdraw.is_applied:
                        status = "Оплачен"
                    
                    end_msg += f"<i>{withdraw.withdraw_id} - {withdraw.withdraw_sum}₽ - {status} - {withdraw.usdt_sum}USDT</i>\n"
            
            end_msg += f"\nОбщая сумма по чекам: <b>{total_cheques_sum}₽</b>\nОбщая сумма по выводам: <b>{total_withdraw_sum}₽</b>\nОбщая прибыль: <b>{total_income}₽</b>"

            await context.bot.send_message(
                    usr.telegram_chat_id,
                    end_msg,
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В начало 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )
        
        elif type_of_oper == "all":
            cheques = Cheque.objects.filter(
                cheque_owner=ApplyUser.objects.filter(username=user_info_about).first(),
            ).all()

            withdraws = Withdraw.objects.filter(
                withdraw_owner=ApplyUser.objects.filter(username=user_info_about).first(),
            ).all()

            total_cheques_sum, total_withdraw_sum, total_income = 0, 0, 0
            end_msg = f"💰 Статистика о пользователе <b>{ApplyUser.objects.filter(username=user_info_about).first().username}</b> за все время:\n\n<b>Чеки:</b>\n"
            
            cnt1, cnt2 = 0, 0

            if len(cheques) == 0:
                end_msg += "🙁 Пока чеков не было."
            else:
                for cheque in cheques:
                    total_cheques_sum += cheque.cheque_sum
                    total_income += cheque.income

                    if not cheque.is_applied and not cheque.is_denied:
                        status = "В работе"
                    elif cheque.is_applied:
                        status = "Принят"
                    else:
                        status = "Не принят"

                    if not cnt1 == os.environ.get("CNT_TO_SHOW_STAT_FOR_ALL_TIME"):
                        end_msg += f"<i>{cheque.cheque_id} - {cheque.cheque_sum}₽ - {status} - {cheque.income}₽</i>\n"
                        cnt1 += 1

            end_msg += "\n<b>Выводы:</b>\n"

            if len(withdraws) == 0:
                end_msg += "🙁 Пока выводов не было."
            else:
                for withdraw in withdraws:
                    total_withdraw_sum += withdraw.withdraw_sum

                    if not withdraw.is_applied:
                        status = "В работе"
                    elif withdraw.is_applied:
                        status = "Оплачен"
                    
                    if not cnt2 == os.environ.get("CNT_TO_SHOW_STAT_FOR_ALL_TIME"):
                        end_msg += f"<i>{withdraw.withdraw_id} - {withdraw.withdraw_sum}₽ - {status} - {withdraw.usdt_sum}USDT</i>\n"
                        cnt2 += 1

            end_msg += f"\nОбщая сумма по чекам: <b>{total_cheques_sum}₽</b>\nОбщая сумма по выводам: <b>{total_withdraw_sum}₽</b>\nОбщая прибыль: <b>{total_income}₽</b>"

            await context.bot.send_message(
                    usr.telegram_chat_id,
                    end_msg,
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="В начало 🔰",
                            callback_data=f"menu",
                        )], 
                        
                    ])
                )

        return ConversationHandler.END

    @check_user_status
    async def _today_metrics(update: Update, context: CallbackContext) -> None:
        """Функция для получения метрик за день для админа

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        total_trans, total_income, total_withdraws = 0, 0, 0

        cheques = Cheque.objects.filter(
            cheque_date__date=timezone.now()
        ).all()

        withdraws = Withdraw.objects.filter(
            withdraw_date__date=timezone.now()    
        ).all()

        for cheque in cheques:
            if cheque.is_applied:
                total_trans += int(cheque.cheque_sum)
                total_income += cheque.income

        for withdraw in withdraws:
            if withdraw.is_applied:
                total_withdraws += withdraw.withdraw_sum

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"🌎 <b>Чеки:</b>\n- Общий оборот: <b>{total_trans}₽</b>\n- Прибыль: <b>{round(total_income, 2)}₽</b>\n- Всего чеков: <b>{len(cheques)} шт.</b>\n\n🌙 <b>Выводы:</b>\n- Общая сумма выводов: <b>{total_withdraws}₽</b>\n- Всего выводов: <b>{len(withdraws)} шт.</b>",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В начало 🔰",
                    callback_data=f"menu",
                )], 
                
            ])
        )

    @check_user_status
    async def _today_hist(update: Update, context: CallbackContext) -> None:
        """Функция для получения статистики за день для юзера

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        cheques = Cheque.objects.filter(
            cheque_owner=ApplyUser.objects.filter(username=usr).first(),
            cheque_date__date=timezone.now()
        ).all()

        withdraws = Withdraw.objects.filter(
            withdraw_owner=ApplyUser.objects.filter(username=usr).first(),
            withdraw_date__date=timezone.now()    
        ).all()

        total_cheques_sum, total_withdraw_sum = 0, 0
        end_msg = f"💰 Статистика за сегодня:\n\n<b>Чеки:</b>\n"
        
        if len(cheques) == 0:
            end_msg += "🙁 Сегодня чеков не было.\n"
        else:
            for cheque in cheques:
                if cheque.is_applied:
                    total_cheques_sum += cheque.cheque_sum

                if not cheque.is_applied and not cheque.is_denied:
                    status = "В работе"
                elif cheque.is_applied:
                    status = "Принят"
                else:
                    status = "Не принят"
            
                end_msg += f"<i>{cheque.cheque_id} - {cheque.cheque_sum}₽ - {status} - {cheque.income}₽</i>\n"
        
        end_msg += "\n<b>Выводы:</b>\n"

        if len(withdraws) == 0:
            end_msg += "🙁 Сегодня выводов не было.\n"
        else:
            for withdraw in withdraws:
                if withdraw.is_applied:
                    total_withdraw_sum += withdraw.withdraw_sum

                if not withdraw.is_applied:
                    status = "В работе"
                elif withdraw.is_applied:
                    status = "Оплачен"
                
                end_msg += f"<i>{withdraw.withdraw_id} - {withdraw.withdraw_sum}₽ - {status} - {withdraw.usdt_sum}USDT</i>\n"
        
        end_msg += f"\nОбщая сумма по чекам: <b>{total_cheques_sum}₽</b>\nОбщая сумма по выводам: <b>{total_withdraw_sum}₽</b>"

        await context.bot.send_message(
                usr.telegram_chat_id,
                end_msg,
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В начало 🔰",
                        callback_data=f"menu",
                    )], 
                    
                ])
            )

    def reg_handlers(self):
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_username_in_stat, "stat"), CommandHandler("stat", self._ask_for_username_in_stat)],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._ask_for_stat)],
                1: [CallbackQueryHandler(self._get_stat, "^stat_")]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(CallbackQueryHandler(self._today_hist, "today_hist"))
        self.application.add_handler(CallbackQueryHandler(self._today_metrics, "metrics"))