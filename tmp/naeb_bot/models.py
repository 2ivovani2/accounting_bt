from django.db import models

import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class NaebBotUser(models.Model):
    """
        Модель, описывающая пользователй
    """
    telegram_chat_id = models.PositiveBigIntegerField(
        verbose_name="ID пользователя",
        null=True,
    )

    username = models.CharField(
        verbose_name="Имя пользователя",
        null=False,
        default="Anonymous",
        max_length=255
    )

    verified_usr = models.BooleanField(
        verbose_name="Верификация пользователя",
        default=False,
    )

    def __str__(self) -> str:
        return self.username
        
    class Meta:
        verbose_name = "Пользователь DeepFake"
        verbose_name_plural = "Пользователи DeepFake"
