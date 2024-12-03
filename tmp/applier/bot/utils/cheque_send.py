from ..applier_bot import ApplierBot
from .imports import *
from .helpers import *

from partners_bot.bot.utils.delayed_func import check_cheque_status

from datetime import datetime, timedelta

from partners_bot.tasks import initialize_bot
from django.conf import settings

import logging, asyncio

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class ChequeWork(ApplierBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app

    @staticmethod
    async def get_partners_bot_instance():
        if settings.PARTNERS_BOT_INSTANCE is None:
            await initialize_bot()
        return settings.PARTNERS_BOT_INSTANCE

    @staticmethod
    async def get_file_url(bot, file_id):
        """Получить полный URL файла по file_id"""
        try:
            # Получаем объект файла
            file = await bot.get_file(file_id)
            full_url = file.file_path
            return full_url
        except Exception as e:
            print(f"Ошибка при получении файла: {e}")
            return None

    @staticmethod
    def effective_message_type(message):
        """Определяет тип медиа сообщения."""
        if message.photo:
            return "photo"
        elif message.document:
            return "document"
        else:
            return "unknown"

    @staticmethod
    def get_extension(media_type):
        """Возвращает расширение файла по типу медиа."""
        extensions = {
            "photo": "jpg",
            "document": "pdf",  # Можно расширить по необходимости
        }
        return extensions.get(media_type, "bin")

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
    async def _send_photo_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Функция пересылки медиа-группы админу через другого бота."""

        async def send_single_media(
            source_bot,
            target_bot,
            message,
            usr,
            amt,
            new_cheque,
            admin,
            context
        ):
            """Отправляет одиночное медиа сообщение админу через целевой бот и удаляет исходное сообщение."""

            try:
                # Получаем URL файла через исходного бота
                file_id = message.photo[-1].file_id if message.photo else message.effective_attachment.file_id
                media_type = ChequeWork.effective_message_type(message)
                file_url = await ChequeWork.get_file_url(source_bot, file_id)
                if not file_url:
                    await target_bot.send_message(
                        usr.telegram_chat_id,
                        "⛔️ Не удалось получить файл для пересылки.",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="🔙 В меню",
                                callback_data="menu",
                            )],
                        ])
                    )
                    return ConversationHandler.END

                # Скачиваем файл
                async with aiohttp.ClientSession() as session:
                    async with session.get(file_url) as resp:
                        if resp.status != 200:
                            await target_bot.send_message(
                                usr.telegram_chat_id,
                                "⛔️ Не удалось скачать файл для пересылки.",
                                parse_mode="HTML",
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton(
                                        text="🔙 В меню",
                                        callback_data="menu",
                                    )],
                                ])
                            )
                            return ConversationHandler.END
                        file_bytes = await resp.read()
                        file_stream = BytesIO(file_bytes)
                        file_stream.name = f"{media_type}.{ChequeWork.get_extension(media_type)}"

                # Создаём InputMedia объект
                if media_type == "photo":
                    media_item = InputMediaPhoto(media=file_stream, caption=message.caption_html)
                elif media_type == "document":
                    media_item = InputMediaDocument(media=file_stream, caption=message.caption_html)
                else:
                    await target_bot.send_message(
                        usr.telegram_chat_id,
                        f"⛔️ Неизвестный тип медиа: {media_type}",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="🔙 В меню",
                                callback_data="menu",
                            )],
                        ])
                    )
                    return ConversationHandler.END

                # Отправляем медиа через целевой бот
                await target_bot.send_media_group(chat_id=admin.telegram_chat_id, media=[media_item])

                # Отправляем сообщение с информацией о платеже
                msg = await target_bot.send_message(
                    admin.telegram_chat_id,
                    f"🤩 Новая оплата по реквизитам <b>{usr.reks.card_number if usr.reks else '🌪️'}</b> - <i>{usr.reks.card_owner_name if usr.reks else '🌪️'}</i> на сумму <b>{amt}</b> рублей.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Принять оплату чека ✅",
                            callback_data=f"acception_cheque_true_{new_cheque.cheque_id}",
                        )],
                        [InlineKeyboardButton(
                            text="Отклонить оплату чека ⛔️",
                            callback_data=f"acception_cheque_false_{new_cheque.cheque_id}",
                        )]
                    ])
                )
                await msg.pin()

                # Уведомляем пользователя об успешной отправке
                await source_bot.send_message(
                    usr.telegram_chat_id,
                    f"✅ Ваш чек был успешно отправлен.\n\n<blockquote>Если хотите повторить операцию, нажмите на соответствующую кнопку</blockquote>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔄 Отправить еще",
                            callback_data="send_cheque",
                        )],
                        [InlineKeyboardButton(
                            text="🔙 В меню",
                            callback_data="menu",
                        )],
                    ])
                )

            except Exception as e:
                print(f"Ошибка при обработке одиночного медиа сообщения: {e}")
                await target_bot.send_message(
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

        async def media_group_sender(
            source_bot,
            target_bot,
            group_id,
            usr,
            amt,
            new_cheque,
            admin,
            context
        ):
            """Отправляет собранную медиа-группу админу через целевой бот и удаляет исходные сообщения."""

            media_groups = context.bot_data.get('media_groups', {})
            media_data = media_groups.pop(group_id, [])

            timers = context.bot_data.get('timers', {})
            timers.pop(group_id, None)

            if not media_data:
                logger.info("Нет медиа для отправки")
                return

            media_to_send = []
            for msg in media_data:
                media_type = msg.get("media_type")
                file_id = msg.get("media_id")
                caption = msg.get("caption")

                # Получаем URL файла через исходного бота
                file_url = await ChequeWork.get_file_url(source_bot, file_id)
                if not file_url:
                    continue

                # Скачиваем файл
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(file_url) as resp:
                            if resp.status != 200:
                                logger.error(f"Не удалось скачать файл по URL: {file_url}")
                                continue
                            file_bytes = await resp.read()
                            file_stream = BytesIO(file_bytes)
                            file_stream.name = f"{media_type}.{ChequeWork.get_extension(media_type)}"
                except Exception as e:
                    logger.error(f"Ошибка при скачивании файла: {e}")
                    continue

                # Создаём InputMedia объект
                if media_type == "photo":
                    media_item = InputMediaPhoto(media=file_stream, caption=caption)
                elif media_type == "document":
                    media_item = InputMediaDocument(media=file_stream, caption=caption)
                else:
                    logger.error(f"Неизвестный тип медиа: {media_type}")
                    continue

                media_to_send.append(media_item)

            if not media_to_send:
                logger.info("Нет медиа для отправки после обработки")
                return

            try:
                await target_bot.send_media_group(chat_id=admin.telegram_chat_id, media=media_to_send)
            except Exception as e:
                logger.error(f"Ошибка при отправке медиа-группы: {e}")
                return

            # Отправляем сообщение с информацией о платеже
            try:
                msg = await target_bot.send_message(
                    admin.telegram_chat_id,
                    f"🤩 Новая оплата по реквизитам <b>{usr.reks.card_number if usr.reks else '🌪️'}</b> - <i>{usr.reks.card_owner_name if usr.reks else '🌪️'}</i> на сумму <b>{amt}</b> рублей.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Принять оплату чека ✅",
                            callback_data=f"acception_cheque_true_{new_cheque.cheque_id}",
                        )],
                        [InlineKeyboardButton(
                            text="Отклонить оплату чека ⛔️",
                            callback_data=f"acception_cheque_false_{new_cheque.cheque_id}",
                        )]
                    ])
                )
                await msg.pin()
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения администратору: {e}")

            # Уведомляем пользователя об успешной отправке
            try:
                await source_bot.send_message(
                    usr.telegram_chat_id,
                    f"✅ Ваши чеки были успешно отправлены.\n\n<blockquote>Если хотите повторить операцию, нажмите на соответствующую кнопку</blockquote>",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="🔄 Отправить еще",
                            callback_data="send_cheque",
                        )],
                        [InlineKeyboardButton(
                            text="🔙 В меню",
                            callback_data="menu",
                        )],
                    ])
                )
            except Exception as e:
                logger.error(f"Ошибка при уведомлении пользователя: {e}")

            # Завершаем разговор
            return ConversationHandler.END

        admin = ApplyUser.objects.filter(username=os.environ.get("ADMIN_TO_APPLY_USERNAME")).first()
        if not admin:
            print("Администратор не найден.")
            return ConversationHandler.END

        usr, _ = await user_get_by_update(update)
        partners_bot = await ChequeWork.get_partners_bot_instance() if usr.reks and not usr.reks.is_emergency else context.bot

        # Получаем сумму чека из user_data
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
            await partners_bot.send_message(
                usr.telegram_chat_id,
                f"⛔️ Во время отправки чека возникла ошибка:\n\n<pre>{e}</pre>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="🔙 В меню",
                        callback_data="menu",
                    )],
                ])
            )
            return ConversationHandler.END

        message = update.effective_message
        group_id = message.media_group_id
        
        if group_id:
            media_type = ChequeWork.effective_message_type(message)
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

            # Используем context.bot_data для хранения медиа-групп
            media_groups = context.bot_data.setdefault('media_groups', {})
            media_groups.setdefault(group_id, []).append(msg_dict)
            
            timers = context.bot_data.setdefault('timers', {})

            if group_id not in timers:
                
                async def delayed_media_group_sender():
                    await asyncio.sleep(2.0)
                    await media_group_sender(
                        source_bot=context.bot,
                        target_bot=partners_bot,
                        group_id=group_id,
                        usr=usr,
                        amt=amt,
                        new_cheque=new_cheque,
                        admin=admin,
                        context=context
                    )

                # Запускаем отложенную задачу без блокировки текущего потока
                asyncio.create_task(delayed_media_group_sender())

                timers[group_id] = True  # Отмечаем, что таймер установлен

            run_time = datetime.now() + timedelta(hours=3)
            if usr.reks and not usr.reks.is_emergency:
                settings.SCHEDULER.add_job(check_cheque_status, 'date', run_date=run_time, args=[context.bot, partners_bot, usr, admin, new_cheque, context.bot_data.get("usdt_price", 100.0)])
                
                if settings.SCHEDULER.state != 1:
                    settings.SCHEDULER.start()

            return 1  # Оставляем разговор активным

        else:
            # Обработка одиночного сообщения без медиа-группы
            await send_single_media(
                source_bot=context.bot,
                target_bot=partners_bot,
                message=message,
                usr=usr,
                amt=amt,
                new_cheque=new_cheque,
                admin=admin,
                context=context
            )

            return ConversationHandler.END

    
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

        try:
            new_cheque = Cheque.objects.filter(cheque_id=query.data.split("_")[-1]).first()
            amount, status = new_cheque.cheque_sum, query.data.split("_")[-2]

            user_to_update = new_cheque.cheque_owner

            if status == "true":
                new_cheque.is_applied = True
                user_to_update.balance = round(user_to_update.balance, 2) + round(float(amount) - (float(amount) * user_to_update.comission * 0.01), 2)
                user_to_update.save()

                if Ref.objects.filter(whom_invited=user_to_update).exists():
                    ref_relation = Ref.objects.filter(whom_invited=user_to_update).first()
                    ref_relation.ref_income += int(amount) * 0.01 * int(os.environ.get("REF_PERCENT", 1))
                    ref_relation.save()

                    who_invited = ref_relation.who_invited
                    who_invited.balance = round(who_invited.balance, 2) + round(float(amount) * 0.01 * int(os.environ.get("REF_PERCENT", 1)), 2)
                    who_invited.save()

                    await context.bot.send_message(
                        who_invited.telegram_chat_id,
                        f"💰 <i>НОВОЕ ПОСТУПЛЕНИЕ</i> 💰\n\n<blockquote>• Ваш реферал - <b>{user_to_update.username}</b>\n• Сумма чека - <b>{new_cheque.cheque_sum}</b>\n• Ваша прибыль - <b>{int(int(new_cheque.cheque_sum) * 0.01 * int(os.environ.get('REF_PERCENT', 1)))}₽</b></blockquote>\n\nСумма уже зачислена на ваш баланс.",
                        parse_mode="HTML",
                    )

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

            else:
                new_cheque.is_denied = True
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"⚔️ Вы отклонили чек <b>{new_cheque.cheque_id}</b> от <b>{new_cheque.cheque_owner.username}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}</b>.",
                    parse_mode="HTML",
                )

                await context.bot.send_message(
                    user_to_update.telegram_chat_id,
                    f"📛К сожалению, ваш(и) чек(и) <b>{new_cheque.cheque_id}</b> на сумму <b>{new_cheque.cheque_sum}₽</b> от <b>{str(new_cheque.cheque_date).split('.')[:1][0]}(МСК)</b> был отклонен.",
                    parse_mode="HTML",
                    reply_markup = None
                )

            new_cheque.save()
            
        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"💣 Возникла ошибка.\n\nОшибка: <i>{e}</i>",
                parse_mode="HTML",
            )

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
