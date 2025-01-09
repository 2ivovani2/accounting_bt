from .utils.imports import *
from .utils.helpers import *


class ApplierBot:
    
    def __init__(self) -> None:
        """
            Инициализация апа
        """
            
        self.application = (
            ApplicationBuilder()
            .token(os.environ.get('APPLIER_BOT_TOKEN'))
            .build()
        )

    async def _start(self, update: Update, context: CallbackContext):
        """
            Обработчик команды /start

            Returns:
                Завершает диалог, путем вызова ConversationHandler.END
        """

        usr, created = await user_get_by_update(update)
        
        if context.args and created:
            try:
                ref_id = int(context.args[0])
                if ApplyUser.objects.filter(telegram_chat_id=ref_id).exists():
                    who_invited = ApplyUser.objects.filter(telegram_chat_id=ref_id).first()
                    Ref(
                        who_invited=who_invited,
                        whom_invited=usr
                    ).save()
            except:
                pass


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
                    f"<b>Приветствую, партнер 💎</b>\nПеред началом работы, ознакомьтесь с условиями и правилами <b>DRIP MONEY</b>\n\n<a href='https://t.me/{os.environ.get('ADMIN_TO_APPLY_USERNAME')}'>Тех. поддержка</a> / <a href='{os.environ.get('NEWS_LINK')}'>Новостной канал</a>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                text="💰 Отправить чек",
                                callback_data="send_cheque",
                            ),
                            InlineKeyboardButton(
                                text="💎 Профиль",
                                callback_data="profile",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                text="📄 Условия",
                                url=f"{os.environ.get('DOC_LINK')}"
                            )
                        ]
                    ])
                )
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"🤩 <b>{usr.username}</b>, приветик!",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Статистика 📊",
                            callback_data="stat",
                        )],
                        [InlineKeyboardButton(
                            text="Метрики дня ⭐️",
                            callback_data="metrics",
                        )],
                        [InlineKeyboardButton(
                            text="Установить курс 💲",
                            callback_data="set_course",
                        )],
                        [InlineKeyboardButton(
                            text="Админка 👀",
                            web_app=WebAppInfo(url=f"{os.environ.get('DOMAIN_NAME')}/admin")
                        )]
                    ])
                )

        return ConversationHandler.END
    
    @check_user_status
    async def _profile(update: Update, context: CallbackContext) -> None:
        """Функция просмотра профиля юзера

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        
        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
        
        total_money = 0
        for cheque in Cheque.objects.filter(cheque_owner=usr).all():
            total_money += cheque.cheque_sum * (1 - usr.comission * .01)

        if context.bot_data.get("usdt_price", ""):
            course = context.bot_data["usdt_price"]
        else:
            try:
                url = "https://api.binance.com/api/v3/ticker/price"
                params = {
                    "symbol": "USDTRUB"
                }
                response = requests.get(url, params=params)
                ticker_info = response.json()

                if 'price' in ticker_info:
                    course = round(float(ticker_info['price']), 2) + float(os.environ.get("NADBAVKA"))
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

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"<b>Ⓘ <u>ID профиля</u></b> - {usr.telegram_chat_id}\n\n· Текущий баланс: <b>{usr.balance}₽</b>\n· Заработано: <b>{round(total_money, 1)}₽</b>\n· Текущая комиссия: <b>{usr.comission}%</b>\n· Курс USDT/RUB: <b>{course}₽</b>\n\n<b>Возникли тех неполадки ⤵️</b> @{os.environ.get('ADMIN_TO_APPLY_USERNAME')}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    
                    InlineKeyboardButton(
                        text="⌛️ Вывод", 
                        callback_data="withdraw_menu"
                    ),
                    InlineKeyboardButton(
                        text="💸 Отправить чек", 
                        callback_data="send_cheque"
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text="📆 История",
                        callback_data="today_hist",
                    ),
                    InlineKeyboardButton(
                        text="💵 Реквизиты", 
                        callback_data="reks"
                    ),
                
                ],
                [
                    InlineKeyboardButton(
                        text="🔗 Рефералы", 
                        callback_data="refs"
                    ),
                    InlineKeyboardButton(
                        text="🔙 Назад", 
                        callback_data="menu"
                    )
                ],
            ])
        )

    @check_user_status
    async def _reks_info(update: Update, context: CallbackContext) -> None:
        """Функция просмотра профиля юзера

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        if usr.reks:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🔴 Ваши актуальные реквизиты:\n\n<pre>{usr.reks.card_number} - {usr.reks.sbp_phone_number} - {usr.reks.card_owner_name} - {usr.reks.bank_name}</pre>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад", 
                            callback_data="profile"
                        )
                    ]
                ])
            )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🥶 У вас пока нет актуальных реквизитов, если произошла ошибка, то обратитесь к администратору.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            text="🤩 Получить реквизиты", 
                            callback_data="get_reks"
                        ),
                    ] if not usr.reks else [],
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад", 
                            callback_data="profile"
                        )
                    ]
                ])
            )

    @check_user_status
    async def _get_reks(update: Update, context: CallbackContext) -> None:
        """Функция просмотра профиля юзера

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        free_processor = Processor.objects.filter(insurance_deposit__gte=10000)
        if free_processor.exists():
            free_reks = Reks.objects.filter(reks_owner=free_processor.first(), is_archived=False)
            if free_reks.exists():
                usr.reks = free_reks.first()
                usr.save()
             
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"💸 Мы подобрали подходящие для вас реквизиты, вы можете найти их в разделе <b>'Реквизиты'</b>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад", 
                                callback_data="profile"
                            )
                        ]
                    ])
                )
            
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"😭 К сожалению, нам не удалось найти подходящие для вас реквизиты. Попробуйте позже.\n\n<blockquote>Если вам <b>срочно</b> необходимы реквизиты, то обратитесь к технической поддержке для оперативного решения вашего вопроса.</blockquote>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                text="🔙 Назад", 
                                callback_data="profile"
                            )
                        ]
                    ])
                )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"😭 К сожалению, нам не удалось найти подходящие для вас реквизиты. Попробуйте позже.\n\n<blockquote>Если вам <b>срочно</b> необходимы реквизиты, то обратитесь к технической поддержке для оперативного решения вашего вопроса.</blockquote>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            text="🔙 Назад", 
                            callback_data="profile"
                        )
                    ]
                ])
            )


    @check_user_status
    async def _refs_info(update: Update, context: CallbackContext) -> None:
        """Функция просмотра профиля юзера

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)

        query = update.callback_query
        if query:
            await query.answer()
            await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)

        usr_refs_relations = Ref.objects.filter(who_invited=usr).all()
        total_ref_income = sum([ref.ref_income for ref in usr_refs_relations])

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"💳 Пригласив нового клиента, вы сможете получать <b>{os.environ.get('REF_PERCENT', 1)}%</b> от его оборота.\n\n<blockquote>🔗 Ваша персональная ссылка: https://t.me/{context.bot.username}?start={usr.telegram_chat_id}</blockquote>\n\nВсего приглашено рефералов: <b>{len(usr_refs_relations)} шт.</b>\nВсего заработано с рефералов: <b>{total_ref_income}₽</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        text="🔙 Назад", 
                        callback_data="profile"
                    )
                ]
            ])
        )

    @check_user_status
    async def _ask_for_course_from_admin(update: Update, context: CallbackContext) -> None:
        """Функция узначи курса

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        await context.bot.send_message(
            usr.telegram_chat_id,
            f"😀 Введите курс, который установим.",
            parse_mode="HTML",
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В начало 🔰",
                    callback_data=f"menu",
                )], 
                
            ])
        )

        return 0

    @check_user_status
    async def _set_course(update: Update, context: CallbackContext) -> None:
        """Функция узначи курса

        Args:
            Update (_type_): объект update
            context (CallbackContext): объект context
        """ 
        
        usr, _ = await user_get_by_update(update)
        try:
            course = round(float(update.message.text.strip()), 2)
            context.bot_data["usdt_price"] = course
         
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤩 Вы успешно установили курс <b>{course}</b>",
                parse_mode="HTML",
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В начало 🔰",
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
                        text="В начало 🔰",
                        callback_data=f"menu",
                    )], 
                ])
            )

        return ConversationHandler.END

    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию хэндлеров в приложении
        """

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_course_from_admin, "set_course")],
            states={
                0: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._set_course)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)],
            conversation_timeout=300
        ))

        self.application.add_handler(CallbackQueryHandler(self._profile, "profile"))
        self.application.add_handler(CallbackQueryHandler(self._refs_info, "refs"))
        self.application.add_handler(CallbackQueryHandler(self._reks_info, "reks"))
        self.application.add_handler(CallbackQueryHandler(self._get_reks, "get_reks"))
        
        return self.application

    def set_last_handlers(self, application):
        application.add_handler(CommandHandler("start", self._start))
        application.add_handler(CallbackQueryHandler(self._start, "menu"))

        from django.conf import settings
        settings.CLIENT_APPLICATION = application
        settings.CLIENT_BOT_INSTANCE = application.bot

        return application



