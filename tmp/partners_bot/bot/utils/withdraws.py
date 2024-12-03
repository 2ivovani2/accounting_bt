from ..processors_bot import ProcessorsBot
from .imports import *
from .helpers import *

import logging 

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class PartnersWithdraws(ProcessorsBot):
    def __init__(self, app) -> None:
        super().__init__()
        self.application = app
    