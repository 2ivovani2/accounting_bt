from django.db import models
from django.contrib.auth.models import AbstractUser
from decimal import Decimal, ROUND_HALF_UP

class Processor(AbstractUser):
    """
        Модель, описывающая пользователй DM_partners
    """

    telegram_chat_id = models.PositiveBigIntegerField(
        verbose_name="ID пользователя",
        null=True,
    )

    password = models.CharField(
        max_length=128,
        null=True,
        blank=True
    ) 

    verified_usr = models.BooleanField(
        verbose_name="Верификация пользователя",
        default=False
    )

    is_superuser = models.BooleanField(
        verbose_name="Явлется ли юзер админом",
        default=False
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

    is_ready_to_get_money_first = models.BooleanField(
        verbose_name="Первичная идентификация",
        default=False
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
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    is_archived = models.BooleanField(
        verbose_name="Флаг для проверки не добавляет ли процессор такие же реквизиты.",
        default=False
    )

    is_emergency = models.BooleanField(
        verbose_name="Являются ли реквизиты резервными",
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
        return f"{self.reks_owner.username} {self.card_number}"
    
    class Meta:
        verbose_name = "Реквизит"
        verbose_name_plural = "Реквизиты"

class AutoAcceptCheque(models.Model):
    """
    Модель, описывающая чеки, которые принимаются автоплатежкой
    """
    hash = models.CharField(
        verbose_name="Хэш для чека",
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )
    amount = models.DecimalField(
        verbose_name="Сумма чека",
        max_digits=10,
        decimal_places=2,
        null=True
    )
    description = models.TextField(
        verbose_name="Описание платежа",
        max_length=300,
        null=True,
        blank=True
    )
    reks = models.ForeignKey(
        Reks,
        verbose_name="Реквизиты для юзера",
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания",
        auto_now_add=True
    )

    is_applied = models.BooleanField(
        verbose_name="Принят ли чек",
        default=False
    )

    success_webhook = models.CharField(
        verbose_name="Ссылка отправки принятия чека", 
        max_length=255,
        null=True,
        blank=True,
    )

    redirect_url = models.CharField(
        verbose_name="Ссылка отправки непринятия чека", 
        max_length=255,
        null=True,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.amount is not None:
            self.amount = self.amount.quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cheque {self.hash} - {self.amount}"

    class Meta:
        verbose_name = "Автопринятый чек"
        verbose_name_plural = "Автопринятые чеки"

class InsurancePayment(models.Model):
    """
        Модель, описывающая страховые оплаты DM_partners
    """
    owner = models.ForeignKey(
        Processor,
        verbose_name="Владелец оплаты",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
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
