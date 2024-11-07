from ..applier_bot import ApplierBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class WithdrawsWork(ApplierBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
    
    @check_user_status
    async def _withdraw_menu(update: Update, context: CallbackContext) -> None:
        """ Многофункциональное меню для выбора типа вывода
        
            Args:
                Update (_type_): объект update
                context (CallbackContext): объект context
        """ 

        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"<b>Ⓘ Вывод денежных средств</b>\n<blockquote>Выберите удобный для вас способ вывода\nЕсли выбирайте вывод на иностранные реквизиты, деньги будут конвертированы по курсу bybit/okx\nУчитывайте, что мы автоматически спишем доп комиссию в виде 2$ при выводе на USDT TRC20 (комиссия сети) </blockquote>\n\nВаш баланс: <b>{usr.balance}₽</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text="💰 USDT TRC20",
                        callback_data="get_money_crypto"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="💳 Карта",
                        callback_data="get_money_fiat"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", 
                        callback_data="profile"
                    )
                ]
            ])
        )

    @check_user_status
    async def _ask_for_money_withdraw(update: Update, context: CallbackContext) -> None:
        """Функция формирования заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        query = update.callback_query
        await query.answer()
        
        type_of_withdraw = query.data.split("_")[-1]

        if usr.has_active_withdraw and Withdraw.objects.filter(withdraw_owner=usr, is_applied=False).exists():
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"📛 К сожалению, вы не можете подавать заявку на вывод, пока прошлый ордер не будет исполнен.\n\n<blockquote>Если у вас срочное обращение, то нажмите на кнопку ниже и обратитель к админиcтартору.</blockquote>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🆘 Помощь",
                        url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                    )],
                    [InlineKeyboardButton(
                        text="🔙 Назад",
                        callback_data="menu",
                    )],
                ])
            )
        else:
            if int(usr.balance) >= int(os.environ.get("MIN_SUM_TO_WITHDRAW")):
                if type_of_withdraw == "crypto":
                    context.user_data["withdraw_type"] = "crypto"
                    price = context.bot_data.get("usdt_price", None)
                    
                    if not price:
                        try:
                            url = "https://api.binance.com/api/v3/ticker/price"
                            params = {
                                "symbol": "USDTRUB"
                            }
                            response = requests.get(url, params=params)
                            ticker_info = response.json()

                            if 'price' in ticker_info:
                                context.user_data["usdt_price"] = round(float(ticker_info['price']), 2) + float(os.environ.get("NADBAVKA"))
                                await context.bot.send_message(
                                    usr.telegram_chat_id,
                                    f"🤩 Отправьте свой адрес для приема <b><u>USDT</u></b> в сети <b><u>TRC20</u></b>.\n\n<blockquote>ВАЖНО!! Если вы введете неверный адрес, то ваши средства могут быть утеряны.</blockquote>",
                                    parse_mode="HTML",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton(
                                            text="🔙 Назад",
                                            callback_data="profile",
                                        )],
                                    ])
                                )

                                return 0

                            else:
                                await context.bot.send_message(
                                    usr.telegram_chat_id,
                                    f"⛔️ Возникла ошибка во время получения цены <b>USDT/RUB</b>.\n\nЕсли проблема повторяется, обратитеь к администратору.",
                                    parse_mode="HTML",
                                    reply_markup=InlineKeyboardMarkup([
                                        [InlineKeyboardButton(
                                                text="💎 В меню",
                                                callback_data="menu",
                                        )],
                                        [InlineKeyboardButton(
                                                text="🆘 Администратор",
                                                url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                                        )],
                                    ])
                                )

                        except Exception as e:
                            usr.has_active_withdraw = False
                            usr.save()
                            
                            await context.bot.send_message(
                                usr.telegram_chat_id,
                                f"⛔️ Возникла ошибка во время получения цены <b>USDT/RUB</b>.\n\nОшибка: <i>{e}</i>",
                                parse_mode="HTML",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton(
                                            text="💎 В меню",
                                            callback_data="menu",
                                    )],
                                    [InlineKeyboardButton(
                                            text="🆘 Администратор",
                                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                                    )],
                                ])
                            )
                    else:
                        context.user_data["usdt_price"] = price
                        
                        await context.bot.send_message(
                            usr.telegram_chat_id,
                            f"🤩 Отправьте свой адрес для приема <b><u>USDT</u></b> в сети <b><u>TRC20</u></b>.\n\nВАЖНО!! Если вы введете неверный адрес, то ваши средства могут быть утеряны.",
                            parse_mode="HTML",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton(
                                    text="🔙 Назад",
                                    callback_data="menu",
                                )],
                            ])
                        )

                        return 0
                else:
                    context.user_data["withdraw_type"] = "fiat"
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"💳 Отправьте номер карты и рядом банк получателя.\n\n<blockquote>ВАЖНО!! Если вы введете неверный номер, то ваши средства могут быть утеряны.</blockquote>",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="🔙 Назад",
                                callback_data="menu",
                            )],
                        ])
                    )

                    return 0

            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"📛К сожалению, вы не можете вывести менее <b>{os.environ.get('MIN_SUM_TO_WITHDRAW')}₽</b>.\n\n<blockquote>Если у вас срочное обращение, то нажмите на кнопку ниже и обратитель к админиcтартору.</blockquote>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад",
                                callback_data="menu",
                            ),
                            InlineKeyboardButton(
                                text="🆘 Помощь",
                                url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                            )
                        ],
                    ])
                )

            return ConversationHandler.END

    @check_user_status
    async def _send_withdraw_appliment(update: Update, context: CallbackContext) -> None:
        """Функция для подтверждения заявки для вывода

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        withdraw_type = context.user_data.get("withdraw_type", None)
        if withdraw_type == "crypto":
            usdt_address = update.message.text.strip()

            def is_trc20_address(address):
                if len(address) != 34:
                    return False
                if address[0] != 'T':
                    return False
                try:
                    decoded = base58.b58decode_check(address)
                    if len(decoded) == 21:
                        return True
                except ValueError:
                    return False
                return False

            if is_trc20_address(usdt_address):
                context.user_data['usdt_address'] = usdt_address
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"Вы отравили неверный адрес. Проверьте, что вы отправили адрес <b>USDT</b> в сети <b>TRC-20</b>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔙 Назад",
                            callback_data="menu",
                        )],
                    ])
                )
                return ConversationHandler.END

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"Вы запросили вывод:\n\n✔️ Сумма: <b>{usr.balance - (usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance)}₽</b>\n✔️ Курс: <b>{context.user_data['usdt_price']}₽</b>\n✔️ Адрес TRC-20: <i>{context.user_data['usdt_address']}</i>\n\nИтог: <b><u>{round(((usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance) / context.user_data['usdt_price']) - 2.00, 2)} USDT</u></b>\n\n* <i>2$ - комиссия на вывод USDT самой биржи.</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                            text="✅ Подтверждаю",
                            callback_data="apply_withdraw",
                    )],
                    [InlineKeyboardButton(
                            text="❌ Отменить",
                            callback_data="profile",
                    )],
                ])
            )
        elif withdraw_type == "fiat":
            card_number = update.message.text.strip()
            context.user_data["card_number"] = card_number
            
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"Вы запросили вывод:\n\n✔️ Сумма: <b>{(usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance)}₽</b>\n💳 Реквизиты: <pre>{card_number}</pre>\n\n* <i>Может взиматься комиссия на вывод банков.</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                            text="✅ Подтверждаю",
                            callback_data="apply_withdraw",
                    )],
                    [InlineKeyboardButton(
                            text="❌ Отменить",
                            callback_data="profile",
                    )],
                ])
            )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🟥 К сожалению, не удается подтвердить информацию. Если ошибка повторяется, обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                            text="💎 В меню",
                            callback_data="menu",
                    )],
                    [InlineKeyboardButton(
                            text="🆘 Помощь",
                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                    )],
                ])
            )

        return ConversationHandler.END

    @check_user_status
    async def _send_withdraw_appliment_to_admin(update: Update, context: CallbackContext) -> None:
        """Функция для отправки админу заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()
        
        query = update.callback_query
        await query.answer()
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        usr.has_active_withdraw = True
        usr.save()


        withdraw_type = context.user_data.get("withdraw_type", None)
        if withdraw_type == "crypto":
            try: 
                logging.info("---------------------------------")
                logging.info(usr.balance)
                logging.info(context.user_data["usdt_price"])
                logging.info((usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance))
                logging.info(((usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance) / context.user_data['usdt_price']))
                logging.info(round(((usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance) / context.user_data['usdt_price']) - 2.00, 2))
                logging.info("---------------------------------")

                order = Withdraw(
                    withdraw_id = f"#{secrets.token_urlsafe(int(os.environ.get('IDS_LEN')))}".replace("_", ""),
                    withdraw_sum = round(usr.balance, 2) - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * round(usr.balance, 2),
                    withdraw_owner = usr,
                    withdraw_address = context.user_data["usdt_address"],
                    course = context.user_data["usdt_price"],
                    usdt_sum = round(((usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance) / context.user_data['usdt_price']) - 2.00, 2)
                )

                order.save()

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"Заявка <b>{order.withdraw_id}</b> успешно создана\n\n<blockquote>Ожидайте вывода, обычно это занимает от 3-6 часов.\nВывод производится в вечернее время.</blockquote>",
                    parse_mode="HTML",
                )
                
                msg = await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"<b>{usr.username}</b> запросил вывод <b>{order.withdraw_id}</b>:\n\n✔️ Сумма: <b>{order.withdraw_sum}₽</b>\n✔️ Курс: <b>{context.user_data['usdt_price']}₽</b>\n✔️ Адрес TRC-20: <i>{context.user_data['usdt_address']}</i>\n\nИтог: <b><u>{order.usdt_sum} USDT</u></b>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Ордер оплачен ✅",
                            callback_data=f"order_paid_{usr.telegram_chat_id}_{order.withdraw_id}",
                        )],
                        [InlineKeyboardButton(
                            text="Отменить ордер 📛",
                            callback_data=f"order_reject_{usr.telegram_chat_id}_{order.withdraw_id}",
                        )],
                    ])
                )

                await msg.pin()

            except Exception as e:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="💎 В меню",
                            callback_data=f"menu",
                        )], 
                        [InlineKeyboardButton(
                            text="🆘 Помощь",
                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                        )],
                    ])
                )
        elif withdraw_type == "fiat":
            try: 
                order = Withdraw(
                    withdraw_id = f"#{secrets.token_urlsafe(int(os.environ.get('IDS_LEN')))}".replace("_", ""),
                    withdraw_sum = round(usr.balance - int(os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2)) * 0.01 * usr.balance, 2),
                    withdraw_owner = usr,
                    withdraw_card_number = context.user_data["card_number"],
                )

                order.save()

                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"Заявка <b>{order.withdraw_id}</b> успешно создана\n\n<blockquote>Ожидайте вывода, обычно это занимает от 3-6 часов.\nВывод производится в вечернее время.</blockquote>",
                    parse_mode="HTML",
                )
                
                msg = await context.bot.send_message(
                    admin.telegram_chat_id,
                    f"<b>{usr.username}</b> запросил вывод <b>{order.withdraw_id}</b>:\n\n✔️ Сумма: <b>{order.withdraw_sum}₽</b>\n💳 Реквизиты: <pre>{order.withdraw_card_number}</pre>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Ордер оплачен ✅",
                            callback_data=f"order_paid_{usr.telegram_chat_id}_{order.withdraw_id}",
                        )],
                        [InlineKeyboardButton(
                            text="Отменить ордер 📛",
                            callback_data=f"order_reject_{usr.telegram_chat_id}_{order.withdraw_id}",
                        )],
                    ])
                )

                await msg.pin()

            except Exception as e:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🆘 Какая-то ошибка возникла.\n\n<i>{e}</i>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="💎 В меню",
                            callback_data=f"menu",
                        )], 
                        [InlineKeyboardButton(
                            text="🆘 Помощь",
                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                        )],
                    ])
                )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🟥 К сожалению, не удается подтвердить информацию. Если ошибка повторяется, обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                            text="💎 В меню",
                            callback_data="menu",
                    )],
                    [InlineKeyboardButton(
                            text="🆘 Помощь",
                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                    )],
                ])
            )

        return ConversationHandler.END

    @check_user_status
    async def _apply_withdraw_appliment(update: Update, context: CallbackContext) -> None:
        """Функция для принятия заявки на вывод

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        query = update.callback_query
        await query.answer()
        
        await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        status, user_id, withdraw_id = query.data.split("_")[-3], query.data.split("_")[-2], query.data.split("_")[-1] 

        if status == "paid":
            try:
                order = Withdraw.objects.filter(withdraw_id=withdraw_id)
                order.update(
                    is_applied=True
                )

                order = order.first()
                user_whom_applied = ApplyUser.objects.filter(telegram_chat_id=user_id).first()
                
                user_whom_applied.balance = round(user_whom_applied.balance, 2) - (round(order.withdraw_sum) + (order.withdraw_sum / (1 - os.environ.get("COMISSION_AMT_FOR_UNLIM_SENDS", 2) * 0.01)))
                user_whom_applied.save()
                
                if order.withdraw_address:
                    await context.bot.send_message(
                        user_whom_applied.telegram_chat_id,
                        f"✅ Заявка на вывод <b>{order.withdraw_id}</b> исполнена!\n\n<blockquote>Сумма в размере {order.usdt_sum}USDT успешно поступили на ваш счет.</blockquote>",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎 В меню",
                                callback_data=f"menu",
                            )], 
                        ])
                    )

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"👅 <b>{usr.username}</b>, вы успешно оплатили <b>{order.withdraw_id}</b> на сумму <b>{order.usdt_sum} USDT</b> от <b>{user_whom_applied.username}</b>.",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎 В меню",
                                callback_data=f"menu",
                            )], 
                        ])
                    )
                else:
                    await context.bot.send_message(
                        user_whom_applied.telegram_chat_id,
                        f"✅ Заявка на вывод <b>{order.withdraw_id}</b> исполнена!\n\n<blockquote>Сумма в размере {order.withdraw_sum}₽ успешно поступили на ваш счет.</blockquote>",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎 В меню",
                                callback_data=f"menu",
                            )],
                        ])
                    )

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"👅 <b>{usr.username}</b>, вы успешно оплатили <b>{order.withdraw_id}</b> на сумму <b>{order.withdraw_sum}₽ фиатом</b> от <b>{user_whom_applied.username}</b>.",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎 В меню",
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
                            text="💎 В меню",
                            callback_data=f"menu",
                        )], 
                        [InlineKeyboardButton(
                            text="🆘 Помощь",
                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                        )],
                    ])
                )
        else:
            try:
                order = Withdraw.objects.filter(withdraw_id=withdraw_id).first()
                user_whom_applied = ApplyUser.objects.filter(telegram_chat_id=user_id).first()
                
                if order.withdraw_address:
                    await context.bot.send_message(
                        user_whom_applied.telegram_chat_id,
                        f"📛 Заявка на вывод <b>{order.withdraw_id}</b> на сумму <b>{order.usdt_sum}USDT</b> отклонена!\n\n<blockquote>Если у вас возникли вопросы, обратитесь к администартору.</blockquote>",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎 В меню",
                                callback_data=f"menu",
                            )], 
                            [InlineKeyboardButton(
                                text="🆘 Помощь",
                                url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                            )],
                            
                        ])
                    )

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"📛 <b>{usr.username}</b>, вы успешно отклонили ордер <b>{order.withdraw_id}</b> на сумму <b>{order.usdt_sum} USDT</b> от <b>{user_whom_applied.username}</b>.",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎В меню",
                                callback_data=f"menu",
                            )], 
                        ])
                    )
                else:
                    await context.bot.send_message(
                        user_whom_applied.telegram_chat_id,
                        f"📛 Заявка на вывод <b>{order.withdraw_id}</b> на сумму <b>{order.withdraw_sum}₽</b> отклонена!\n\n<blockquote>Если у вас возникли вопросы, обратитесь к администартору.</blockquote>",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="💎 В меню",
                                callback_data=f"menu",
                            )], 
                            [InlineKeyboardButton(
                                text="🆘 Помощь",
                                url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                            )],
                            
                        ])
                    )

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"❌ <b>{usr.username}</b>, вы успешно отклонили <b>{order.withdraw_id}</b> на сумму <b>{order.withdraw_sum}₽ фиатом</b> от <b>{user_whom_applied.username}</b>.",
                        parse_mode="HTML",
                        reply_markup = InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="В меню 🔙",
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
                            text="💎 В меню",
                            callback_data=f"menu",
                        )], 
                        [InlineKeyboardButton(
                            text="🆘 Помощь",
                            url=f"https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}"
                        )],
                    ])
                )

        user_whom_applied.has_active_withdraw = False
        user_whom_applied.save()

    def reg_handlers(self):
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_money_withdraw, "^get_money_")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._send_withdraw_appliment)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(CallbackQueryHandler(self._withdraw_menu, "withdraw_menu"))
        self.application.add_handler(CallbackQueryHandler(self._send_withdraw_appliment_to_admin, "apply_withdraw"))
        self.application.add_handler(CallbackQueryHandler(self._apply_withdraw_appliment, "^order_"))
