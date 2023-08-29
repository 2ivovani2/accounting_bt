from django.db import models
from django.contrib.auth.models import AbstractUser

import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class Table(models.Model):
    """
        Модель, описывающая таблицы пользователй
    """

    name = models.CharField(
        verbose_name="Название таблицы",
        max_length=12,
        null=False,
        default="Без названия"
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Таблица"
        verbose_name_plural = "Таблицы"

class Category(models.Model):
    """
        Категория операции по таблице
    """
    CATEGORY_TYPE = (
        ("Доход", "Доход"),
        ("Расход", "Расход"),
    )

    type = models.CharField(
        verbose_name="Тип категории",
        max_length=255,
        choices=CATEGORY_TYPE,
        null=False,
        default="Не определен",
    )

    name = models.CharField(
        verbose_name="Название категории",
        max_length=255,
        null=False,
        default="Без названия"
    )

    table = models.ForeignKey(
        Table,
        verbose_name="Таблица по категории",
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class CustomUser(AbstractUser):
    """
        Модель, описывающая пользователй
    """
    telegram_chat_id = models.PositiveBigIntegerField(
        verbose_name="ID пользователя",
        null=True,
    )

    verified_usr = models.BooleanField(
        verbose_name="Верификация пользователя",
        default=False,
    )

    can_create_tables = models.BooleanField(
        verbose_name="Возможность создавать новые таблицы",
        default=False
    )


    tables = models.ManyToManyField(
        Table,
        verbose_name="Таблицы пользователя",
        blank=True,
    )

    def __str__(self) -> str:
        return self.username
    
    def get_tables(self) -> list:
        """
            Метод, возвращающий все таблицы пользователя
        """
        return [table for table in self.tables.all().order_by("id")]
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class Operation(models.Model):
    """
        Модель, описывающая операции пользователй
    """
    OPERATION_TYPE = (
        ("Доход", "Доход"),
        ("Расход", "Расход"),
    )

    type = models.CharField(
        verbose_name="Тип операции",
        max_length=255,
        choices=OPERATION_TYPE,
        null=False,
        default="Не определен",
    )

    amount = models.BigIntegerField(
        verbose_name="Сумма",
        null=False,
        default=0
    )

    date = models.DateTimeField(
        auto_now_add=True,
        blank=True, 
        verbose_name="Дата поступления"
    )

    table = models.ForeignKey(
        Table,
        verbose_name="Таблица, содержащая данную операцию",
        on_delete=models.CASCADE,
        null=False,
        default="Не определена"
    )

    creator = models.ForeignKey(
        CustomUser,
        verbose_name="Отвественный",
        on_delete=models.SET_NULL,
        null=True,
    )

    category = models.ForeignKey(
        Category,
        verbose_name="Категория операции",
        on_delete=models.SET_NULL,
        null=True,
    )

    description = models.CharField(
        verbose_name="Описание платежа",
        max_length=255,
        null=False,
        default="Без описания"
    )
    

    def __str__(self) -> str:
        return self.creator.username

    class Meta:
        verbose_name = "Операция"
        verbose_name_plural = "Операции"

    