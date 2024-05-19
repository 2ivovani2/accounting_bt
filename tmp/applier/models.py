from django.db import models

class ApplyUser(models.Model):
    """
        Модель, описывающая пользователй TF
    """

    telegram_chat_id = models.PositiveBigIntegerField(
        verbose_name="ID пользователя",
        null=True,
        default="Не определен"
    )

    verified_usr = models.BooleanField(
        verbose_name="Верификация пользователя",
        default=False
    )

    is_superuser = models.BooleanField(
        verbose_name="Явлется ли юзер админом",
        default=False
    )


    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=255,
        null=False,
        default="Anonim"
    )

    def __str__(self) -> str:
        return self.username
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
