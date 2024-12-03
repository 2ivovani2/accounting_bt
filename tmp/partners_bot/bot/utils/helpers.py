from .imports import *

@sync_to_async
def user_get_by_update(update: Update):
    
    """ Функция обработчик, возвращающая django instance пользователя

    Returns:
        _type_: instance, created
    """

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if not message.chat.username:
        username = "Аноним"
    else:
        username = message.chat.username

    instance, created = Processor.objects.update_or_create(
        username = username,
        telegram_chat_id = message.chat.id,
    )
    
    return instance, created

def check_user_status(function):
    """
        Функция декоратор для проверки аутентификации пользователя
    """
    
    async def wrapper(self, update: Update, context:CallbackContext):   
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message

        if not message.chat.username:
            username = "Спидозная козявка"
        else:
            username = message.chat.username

        usr, _ = Processor.objects.update_or_create(
            telegram_chat_id = message.chat.id,
            username=username
        )

        if usr.is_superuser:
            return await function(update, context)

        if usr.verified_usr:
            if usr.is_ready_to_get_money_first:
                return await function(update, context)
            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"😔 Уважаемый <b>{usr.username}</b>, для активации профиля, необходимо внести страховой депозит.\nМинимальная сумма депозита - <b>10.000₽</b>.\n<b>‼️ Обратите внимание</b>, вы не сможете заливаться больше страхового депозита, пока не выведите баланс.\nДля удобной работы, советуем внести сумму выше, чтобы не делать более <b>1-3</b> выводов в день.\n\n<blockquote>Курс устанавливается по 1-2 предложению в ByBit, раздел SBP/SBER/RAIFFEISEN💸</blockquote>",
                    parse_mode="HTML",
                    reply_markup = InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="💶 Страховой депозит",
                            callback_data="insurance_deposit",
                        )]
                    ])
                )
        else:
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
        
    return wrapper
