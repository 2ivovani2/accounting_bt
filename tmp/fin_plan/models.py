from django.db import models
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class User(models.Model):
    """
        Класс, описывающий пользователей финансового бота
    """

    USER_TYPE = (
        ("Админ", "Админ"),
        ("Манагер", "Манагер"),
        ("Воркер", "Воркер"), 
        ("Низшая форма жизни", "Низшая форма жизни"), 
        
    )

    type = models.CharField(
        verbose_name="Тип пользователя",
        max_length=255,
        choices=USER_TYPE,
        null=False,
        default="Низшая форма жизни",
    )

    telegram_chat_id = models.PositiveBigIntegerField(
        verbose_name="ID пользователя",
        null=True,
    )
    
    username = models.CharField(
        verbose_name="Имя пользователя",
        max_length=255,
        null=False,
        default="Аноним 🗿",

    )

    invite_code_limits = models.IntegerField(
        verbose_name="Количество созданий инвайт кодов",
        null=False,
        default=0
    )

    can_create_tasks = models.BooleanField(
        verbose_name="Возможность ставить задачи",
        default=False,
    )

    verified_usr = models.BooleanField(
        verbose_name="Верификация пользователя",
        default=False,
    )
    
    is_superuser = models.BooleanField(
        verbose_name="Является ли юзер админом", 
        default=False,
    )

    def __str__(self) -> str:
        return self.username

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

class Project(models.Model):
    """
        Класс, описывающий все возможные проекты
    """
     
    name = models.CharField(
        verbose_name="Название проекта",
        max_length=255,
        null=False,
        default="💣 Проект"
    ) 

    users = models.ManyToManyField(
        User,
        verbose_name="Пользователи проекта",
        blank=True,
    )

    creator = models.ForeignKey(
        User,
        related_name="creator_of_project",
        verbose_name="Создатель проекта",
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"

class Task(models.Model):
    """
        Класс, описывающий задачу которую надо выполнить
    """

    name = models.CharField(
        verbose_name="Название задачи",
        max_length=255,
        null=False,
        default="Безымянная 🌚"
    )

    description = models.TextField(
        verbose_name="Описание задачи",
        null=False,
        default="Без описания"
    )

    responsible = models.ForeignKey(
        User,
        related_name="responsible_for_task",
        verbose_name="Ответственный",
        on_delete=models.CASCADE,
        null=True,
    )

    task_creator = models.ForeignKey(
        User,
        related_name="creator_of_task",
        verbose_name="Создатель задачи",
        on_delete=models.CASCADE,
        null=True,
    )

    project = models.ForeignKey(
        Project,
        related_name="project_of_task",
        verbose_name="Проект, в который добавить задачу",
        on_delete=models.CASCADE,
        null=True
    )

    deadline = models.DateTimeField(
        verbose_name="Дедлайн задачи",
        null=True,
        editable=True
    )

    def __str__(self) -> str:
        return self.name
    
    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"

class Invite(models.Model):
    """
        Класс описывающий Invite коды для пользователей
    """

    INVITE_TYPE = (
        ("Манагер", "Манагер"),
        ("Воркер", "Воркер"), 
        ("Низшая форма жизни", "Низшая форма жизни")
    )

    code = models.CharField(
        verbose_name="Инвайт код",
        max_length=255,
        null=True,
    )

    creator = models.ForeignKey(
        User,
        related_name="creator_of_invite_token",
        verbose_name="Создатель инвайта",
        on_delete=models.CASCADE,
        null=True,
    )

    valid = models.BooleanField(
        verbose_name="Валидность инвайт кода",
        default=True,
    )

    activator = models.ForeignKey(
        User,
        related_name="activator_of_invite_token",
        verbose_name="Активатор инвайта",
        on_delete=models.CASCADE,
        null=True,
    )

    project = models.ForeignKey(
        Project,
        related_name="project_of_invite_code",
        verbose_name="Проект, в который добавить человека",
        on_delete=models.SET_NULL,
        null=True
    )

    invite_type = models.CharField(
        verbose_name="Тип инвайта",
        max_length=255,
        choices=INVITE_TYPE,
        null=False,
        default="Низшая форма жизни",
    )

    def __str__(self) -> str:
        return self.invite_type
    
    class Meta:
        verbose_name = "Инвайт код"
        verbose_name_plural = "Инвайт коды"