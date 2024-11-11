#partners_bot
import json
from telegram import Update
import logging

logger = logging.getLogger(__name__)

partners_bot_instance = None
partners_application = None

async def initialize_bot():
    global partners_bot_instance, partners_application
    if partners_bot_instance is None:
        from partners_bot.bot.processors_bot import ProcessorsBot  # Import here to avoid circular imports
        partners_bot_instance = ProcessorsBot()
        partners_application = partners_bot_instance.register_handlers()

        # Register additional handlers
        from partners_bot.bot.utils.auth_sys import Auth
        from partners_bot.bot.utils.insurance import Insurance
        from partners_bot.bot.utils.reks import ReksModule

        Insurance(partners_application).reg_handlers()
        Auth(partners_application).reg_handlers()
        ReksModule(partners_application).reg_handlers()

        partners_application = partners_bot_instance.set_last_handlers(partners_application)

        # Initialize the application
        await partners_application.initialize()
        
# Asynchronous function to handle updates
async def handle_update(update_data):
    await initialize_bot()
    try:
        # Decode the update data from JSON
        update_json = json.loads(update_data)
        update = Update.de_json(update_json, partners_application.bot)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to create Update object: {e}")
        return

    # Asynchronously process the update
    try:
        await partners_application.process_update(update)
    except Exception as e:
        logger.error(f"Error processing update: {e}")