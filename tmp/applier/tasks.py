# bot/tasks.py
import asyncio
import json
from celery import shared_task
from telegram import Update, Bot
from applier.bot.applier_bot import ApplierBot
import logging, os

logger = logging.getLogger(__name__)

# Инициализация бота и приложения один раз при загрузке модуля
bot_instance = ApplierBot()
application = bot_instance.register_handlers()

# Регистрация дополнительных хэндлеров
from applier.bot.utils.cheque_send import ChequeWork
from applier.bot.utils.withdraws import WithdrawsWork
from applier.bot.utils.auth_sys import Auth
from applier.bot.utils.metrics import Metrics


Auth(application).reg_handlers()
ChequeWork(application).reg_handlers()
WithdrawsWork(application).reg_handlers()
Metrics(application).reg_handlers()

application = bot_instance.set_last_handlers(application)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

async def initialize_application(app):
    await app.bot.initialize()
    await app.initialize()
    if "messages" not in app.bot_data:
        app.bot_data = {"messages": {}}
    
    await app.start()

loop.run_until_complete(initialize_application(application))

@shared_task
def handle_update(update_data):
    """
    Celery задача для обработки обновлений Telegram.
    """

    try:
        # Декодирование данных обновления из JSON
        update_json = json.loads(update_data)
        update = Update.de_json(update_json, application.bot)
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка декодирования JSON обновления: {e}")
        return
    except Exception as e:
        logger.error(f"Не удалось создать объект Update: {e}")
        return

    # Асинхронная обработка обновления с использованием asyncio
    try:
        loop.run_until_complete(application.process_update(update))
    except Exception as e:
        logger.error(f"Ошибка при обработке обновления: {e}")
