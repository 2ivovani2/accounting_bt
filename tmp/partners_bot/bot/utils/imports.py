from partners_bot.models import *

from asgiref.sync import sync_to_async

import time
from typing import TypedDict, List, Literal, cast
import requests, base58
import os, django, logging, warnings, secrets
warnings.filterwarnings("ignore")

import gspread
import pandas as pd
import numpy as np


from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    WebAppInfo,
    InputMediaPhoto,
    InputMediaDocument,
)

from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ApplicationBuilder,
    PicklePersistence,
)
from telegram.helpers import effective_message_type

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

