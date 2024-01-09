from django.db import models

class TFUser(models.Model):
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

class Telegraph(models.Model):

    creator = models.ForeignKey(
        "tf_maker.TFUser",
        verbose_name="Загрузчик фото",
        on_delete=models.SET_NULL,
        null=True
    )

    date_created = models.DateTimeField(
        verbose_name="Дата создания TF",
        auto_now_add=True,
    )

    link = models.CharField(
        verbose_name="Ссылка на телеграф",
        max_length=255,
        null=False
    )

    def __str__(self) -> str:
        return self.link 

    class Meta:
        verbose_name = "Телеграф"
        verbose_name_plural = "Телеграфы"