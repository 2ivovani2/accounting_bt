#partners_bot
import json
from telegram import Update
import logging
from django.conf import settings


logger = logging.getLogger(__name__)


async def initialize_bot():
    if settings.PARTNERS_BOT_INSTANCE is None:
        from partners_bot.bot.processors_bot import ProcessorsBot  # Import here to avoid circular imports
        settings.PARTNERS_BOT_INSTANCE = ProcessorsBot()
        settings.PARTNERS_APPLICATION = settings.PARTNERS_BOT_INSTANCE.register_handlers()

        # Register additional handlers
        from partners_bot.bot.utils.auth_sys import Auth
        from partners_bot.bot.utils.insurance import Insurance
        from partners_bot.bot.utils.reks import ReksModule
        from partners_bot.bot.utils.cheque import ChequeWork

        Insurance(settings.PARTNERS_APPLICATION).reg_handlers()
        Auth(settings.PARTNERS_APPLICATION).reg_handlers()
        ReksModule(settings.PARTNERS_APPLICATION).reg_handlers()
        ChequeWork(settings.PARTNERS_APPLICATION).reg_handlers()

        settings.PARTNERS_APPLICATION = settings.PARTNERS_BOT_INSTANCE.set_last_handlers(settings.PARTNERS_APPLICATION)

        # Initialize the application
        await settings.PARTNERS_APPLICATION.initialize()
        
# Asynchronous function to handle updates
async def handle_update(update_data):
    await initialize_bot()
    try:
        # Decode the update data from JSON
        update_json = json.loads(update_data)
        update = Update.de_json(update_json, settings.PARTNERS_APPLICATION.bot)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to create Update object: {e}")
        return

    # Asynchronously process the update
    try:
        await settings.PARTNERS_APPLICATION.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")