from django.db import models
from django.utils import timezone

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

    balance = models.PositiveBigIntegerField(
        verbose_name="Баланс пользователя",
        null=False,
        default=0
    )

    comission = models.IntegerField(
        verbose_name="Комиссия пользователя",
        null=False,
        default=8
    )

    def __str__(self) -> str:
        return self.username
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class Cheque(models.Model):
    """
        Модель, описывающая чеки
    """

    cheque_id = models.CharField(
        verbose_name="id чека",
        max_length=255,
        null=False,
        default="#00000"
    )
    
    cheque_sum = models.IntegerField(
        verbose_name="Сумма чека",
        null=False,
        default=0
    )

    cheque_owner = models.ForeignKey(
        ApplyUser,
        verbose_name="Владелец чека",
        on_delete=models.CASCADE,
        null=True,
        default="Не определен"
    )

    cheque_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата поступления"
    )

    is_applied = models.BooleanField(
        verbose_name="Подтвержден ли чек",
        default=False,
    )

    is_denied = models.BooleanField(
        verbose_name="Отклонен ли чек",
        default=False,    
    )

    def __str__(self) -> str:
        return self.cheque_id
    
    class Meta:
        verbose_name = "Чек"
        verbose_name_plural = "Чеки"

class Withdraw(models.Model):
    """
        Модель, описывающая чеки
    """

    withdraw_id = models.CharField(
        verbose_name="id вывода",
        max_length=255,
        null=False,
        default="#00000"
    )
    
    withdraw_sum = models.IntegerField(
        verbose_name="Сумма вывода",
        null=False,
        default=0
    )

    withdraw_owner = models.ForeignKey(
        ApplyUser,
        verbose_name="Владелец вывода",
        on_delete=models.CASCADE,
        null=True,
        default="Не определен"
    )

    withdraw_address = models.CharField(
        verbose_name="Адрес вывода",
        max_length=255,
        null=True
    )

    course = models.FloatField(
        verbose_name="Курс",
        null=False,
        default=0.0
    )

    usdt_sum = models.FloatField(
        verbose_name="Сумма в USDT",
        null=False,
        default=0.0
    )

    withdraw_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата вывода"
    )

    is_applied = models.BooleanField(
        verbose_name="Подтвержден ли вывод",
        default=False,
    )

    income = models.FloatField(
        verbose_name="Наша прибыль",
        null=False,
        default=0
    )

    def __str__(self) -> str:
        return self.withdraw_id
    
    class Meta:
        verbose_name = "Вывод"
        verbose_name_plural = "Выводы"