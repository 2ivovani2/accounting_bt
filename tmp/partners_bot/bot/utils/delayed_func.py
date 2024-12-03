import logging, os
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)
from .imports import *
from applier.models import ApplyUser

async def check_cheque_status(client_bot, partner_bot, client, merchant, cheque, course):
    logging.info(f"🤩 Вызов функции проверки чека {cheque.cheque_id} для {cheque.cheque_owner.username}")
    
    if not cheque.is_applied and not cheque.is_denied:
        cheque.is_applied = True
        cheque.save()

        merchant.balance = round(float(merchant.balance), 2) + cheque.cheque_sum * merchant.comission * 0.01
        merchant.insurnace_deposit -= cheque.cheque_sum        
        merchant.save()

        if merchant.insurance_deposit <= 0:
            client.reks = None
            client.save()

            merchant.is_ready_to_get_money = False
            merchant.save()

            await client_bot.send_message(
                client.telegram_chat_id,
                f"🆘 Ваши реквизиты были изменены, проверьте в разделе <b>Ревизитов</b>, если их там не появилось, то обратитесь к администратору.",
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
            

            await partner_bot.send_message(
                merchant.telegram_chat_id,
                f"😔 Ваш лимит на принятие чеков закончился, вам необходимо вывести <b>{round((merchant.amount_to_accept - merchant.insurance_deposit) / course, 2)}USDT</b> на адрес <pre>{os.environ.get('ACCEPT_INSURANCE_PAYMENTS_ADDRESS','TJbfLnybJxXKoPVrdFfSAGkEoAr1g4DmpW')}</pre>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="menu",
                    )],
                    [InlineKeyboardButton(
                        text="🌪️ Я оплатил",
                        callback_data="reset_insurance_apply",
                    )],
                ])
            )

        await partner_bot.send_message(
            merchant.telegram_chat_id,
            f"🪛 Вы приняли чек <b>{cheque.cheque_id}</b> от <b>{cheque.cheque_owner.username}</b> на сумму <b>{cheque.cheque_sum}₽</b> от <b>{str(cheque.cheque_date).split('.')[:1][0]}</b>.\n\nБаланс обновлен.",
            parse_mode="HTML",
        )

        await client_bot.send_message(
            client.telegram_chat_id,
            f"✅ Чек <b>{cheque.cheque_id}</b> принят!\n• Сумма чека - <b>{cheque.cheque_sum}₽</b>\n• Дата чека - <b>{str(cheque.cheque_date).split('.')[:1][0]}(МСК)</b>\n• Ваша доля - <b>{cheque.cheque_sum - cheque.income}₽</b>\n• Текущий баланс - <b>{client.balance}₽</b>",
            parse_mode="HTML",
            reply_markup = None
        )
    