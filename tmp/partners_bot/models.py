from django.db import models

class Processor(models.Model):
    """
        Модель, описывающая пользователй DM_partners
    """

    telegram_chat_id = models.PositiveBigIntegerField(
        verbose_name="ID пользователя",
        null=True,
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

    balance = models.DecimalField(
        verbose_name="Баланс пользователя",
        null=False,
        default=0.00,
        decimal_places=2,
        max_digits=10
    )

    comission = models.IntegerField(
        verbose_name="Комиссия пользователя",
        null=False,
        default=5
    )

    is_ready_to_get_money = models.BooleanField(
        verbose_name="Может ли юзер принимать деньги на свои реквизиты",
        default=False
    )

    insurance_deposit = models.BigIntegerField(
        verbose_name="Сумма остатка страхового депозита для приема платежей",
        null=False,
        default=0
    )

    amount_to_accept = models.BigIntegerField(
        verbose_name="Сколько процессор готов принимать денег",
        null=False,
        default=0
    )

    info = models.CharField(
        max_length=255,
        null=True,
    )

    has_active_paying_insurance_apply = models.BooleanField(
        verbose_name="Есть ли у юзера заявка на оплату страхового депозита.",
        default=False
    )

    def __str__(self) -> str:
        return self.username
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class Reks(models.Model):
    """
        Модель, описывающая реквизиты DM_partners
    """

    reks_owner = models.ForeignKey(
        Processor,
        verbose_name="Владелец реквизитов",
        on_delete=models.CASCADE,
        null=True,
    )

    is_archived = models.BooleanField(
        verbose_name="Флаг для проверки не добавляет ли процессор такие же реквизиты.",
        default=False
    )

    card_number = models.CharField(
        verbose_name="Номер карты реквизитов",
        max_length=50,
        null=False,
        default="0000 0000 0000 0000",
    )

    sbp_phone_number = models.CharField(
        verbose_name="Номер телефона для принятия по СБП",
        max_length=50,
        null=False,
        default="+79999999999"
    )

    card_owner_name = models.CharField(
        verbose_name="Имя владельца карты",
        max_length=100,
        null=False,
        default="Иванов Иван Иванович"
    )

    bank_name = models.CharField(
        verbose_name="Название банка, которому принадлежит карта.",
        max_length=50,
        null=True
    )


    def __str__(self) -> str:
        return self.reks_owner.username
    
    class Meta:
        verbose_name = "Реквизит"
        verbose_name_plural = "Реквизиты"


class InsurancePayment(models.Model):
    """
        Модель, описывающая страховые оплаты DM_partners
    """
    owner = models.ForeignKey(
        Processor,
        verbose_name="Владелец оплаты",
        on_delete=models.CASCADE,
        null=True,
    )

    payment_sum_rub = models.FloatField(
        verbose_name="Сумма страховой оплаты в рублях",
        null=False,
        default=0.0
    )

    payment_sum_usdt = models.FloatField(
        verbose_name="Сумма страховой оплаты в USDT",
        null=False,
        default=0.0
    )

    is_applied = models.BooleanField(
        verbose_name="Принята ли страховая выплата",
        default=False
    )

    def __str__(self) -> str:
        return self.owner.username
    
    class Meta:
        verbose_name = "Страховка"
        verbose_name_plural = "Страховки"
