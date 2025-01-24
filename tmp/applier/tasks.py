# applier/tasks.py
import json
from telegram import Update
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

async def initialize_bot():
    if settings.CLIENT_BOT_INSTANCE is None:
        from applier.bot.applier_bot import ApplierBot  # Import here to avoid circular imports
        settings.CLIENT_BOT_INSTANCE = ApplierBot()
        settings.CLIENT_APPLICATION = settings.CLIENT_BOT_INSTANCE.register_handlers()

        # Register additional handlers
        from applier.bot.utils.cheque_send import ChequeWork
        from applier.bot.utils.withdraws import WithdrawsWork
        from applier.bot.utils.auth_sys import Auth
        from applier.bot.utils.metrics import Metrics

        Auth(settings.CLIENT_APPLICATION).reg_handlers()
        ChequeWork(settings.CLIENT_APPLICATION).reg_handlers()
        WithdrawsWork(settings.CLIENT_APPLICATION).reg_handlers()
        Metrics(settings.CLIENT_APPLICATION).reg_handlers()

        settings.CLIENT_APPLICATION = settings.CLIENT_BOT_INSTANCE.set_last_handlers(settings.CLIENT_APPLICATION)
        
        await settings.CLIENT_APPLICATION.initialize()
        if "messages" not in settings.CLIENT_APPLICATION.bot_data:
            settings.CLIENT_APPLICATION.bot_data = {"messages": {}}
        
async def handle_update(update_data):
    await initialize_bot()
    try:
        update_json = json.loads(update_data)
        update = Update.de_json(update_json, settings.CLIENT_APPLICATION.bot)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to create Update object: {e}")
        return

    try:
        await settings.CLIENT_APPLICATION.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")