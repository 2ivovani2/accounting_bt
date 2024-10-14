# applier/tasks.py
import json
from telegram import Update
import logging

logger = logging.getLogger(__name__)

# Initialize bot_instance and application as None
bot_instance = None
application = None

async def initialize_bot():
    global bot_instance, application
    if bot_instance is None:
        from applier.bot.applier_bot import ApplierBot  # Import here to avoid circular imports
        bot_instance = ApplierBot()
        application = bot_instance.register_handlers()

        # Register additional handlers
        from applier.bot.utils.cheque_send import ChequeWork
        from applier.bot.utils.withdraws import WithdrawsWork
        from applier.bot.utils.auth_sys import Auth
        from applier.bot.utils.metrics import Metrics

        Auth(application).reg_handlers()
        ChequeWork(application).reg_handlers()
        WithdrawsWork(application).reg_handlers()
        Metrics(application).reg_handlers()

        application = bot_instance.set_last_handlers(application)

        # Initialize the application
        await application.initialize()
        if "messages" not in application.bot_data:
            application.bot_data = {"messages": {}}
        # Do not call application.start() because we're using webhooks

# Asynchronous function to handle updates
async def handle_update(update_data):
    await initialize_bot()
    try:
        # Decode the update data from JSON
        update_json = json.loads(update_data)
        update = Update.de_json(update_json, application.bot)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to create Update object: {e}")
        return

    # Asynchronously process the update
    try:
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")