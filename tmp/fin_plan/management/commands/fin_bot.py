from main.models import *
from fin_plan.models import *

from asgiref.sync import sync_to_async
from rest_framework.authtoken.models import Token

import os, django, logging, warnings, uuid
warnings.filterwarnings("ignore")

from django.core.management.base import BaseCommand

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


@sync_to_async
def user_get_by_update(update: Update):
    """
        Функция обработчик, возвращающая django instance пользователя
    """

    if update.message:
        message = update.message
    else:
        message = update.callback_query.message

    if not message.chat.username:
        username = "Аноним"
    else:
        username = message.chat.username

    instance, created = User.objects.update_or_create(
        username = username,
        telegram_chat_id = message.chat.id,
    )

    return instance, created

def check_user_status(function):
    """
        Функция декоратор для проверки аутентификации пользователя
    """
    async def wrapper(self, update: Update, context:CallbackContext):
        if update.message:
            message = update.message
        else:
            message = update.callback_query.message

        if not message.chat.username:
            username = "Аноним"
        else:
            username = message.chat.username

        usr, _ = User.objects.update_or_create(
            telegram_chat_id = message.chat.id,
            username=username
        )

        if usr.verified_usr:
            return await function(update, context)
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"⛔️ <b>{usr.username}</b>, это приватный бот.\n\nДля того, чтобы им пользоваться вам необходимо активировать инвайт код, полученный от вашего менеджера или админа.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Поддержка 💅🏽",
                        url="https://t.me/i_vovani"
                    )],
                    [InlineKeyboardButton(
                        text="Инвайт код 🔐",
                        callback_data="invite_code"
                    )],
                ])
            )
        
    return wrapper


class Bot:
    """
        Класс, инициализирующий instance бота
    """

    def __init__(self) -> None:
        self.application = Application.builder().token(os.environ.get("FIN_BOT_TOKEN")).build()
        
    @check_user_status
    async def _start(update: Update, context: CallbackContext) -> ConversationHandler.END:
        """
            Обработчик команды /start

        """
        usr, _ = await user_get_by_update(update)
   
        markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Создать инвайт ⭐️",
                    callback_data="create_invite_code",
                )],
                [InlineKeyboardButton(
                    text="Активировать инвайт 😱",
                    callback_data="invite_code",
                )],
                
                [InlineKeyboardButton(
                    text="Создать проект 🍺",
                    callback_data="create_project",
                )] if usr.type.lower() == "админ" else [],


                [InlineKeyboardButton(
                    text="Добавить задачу ➕",
                    callback_data="create_project",
                )] if usr.can_create_tasks else [],


                [InlineKeyboardButton(
                    text="Поддержка 🌻",
                    url="https://t.me/i_vovani"
                )],
                [InlineKeyboardButton(text="Админка 👀", web_app=WebAppInfo(url=f"{os.environ.get('DOMAIN_NAME')}/admin"))] if usr.is_superuser else []
                
            ])

        user_projects = [project.name for project in Project.objects.filter(users__in=[usr]).all()]
        proj_message = ""
        
        if len(user_projects) != 0:
            proj_message += "🤘 <b><u>Ваши проекты:</u></b>\n\n"
            for project in user_projects:
                proj_message += f"🔹 {project}\n" 

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"👋 <b>{usr.username}</b>, доброго времени суток.\n\n🎱 <b><u>Ваш статус</u></b>: <i>{usr.type}</i>\n\n{proj_message}",
            parse_mode="HTML",
            reply_markup=markup
        )
            
        return ConversationHandler.END
    
    def register_handlers(self) -> Application: 
        """
            Метод реализующий регистрацию всех хэндлеров в приложении
        """
        self.application.add_handler(CommandHandler("start", self._start))
        self.application.add_handler(CallbackQueryHandler(self._start, "menu"))

        return self.application

class InviteCodes(Bot):
    """
        Класс, инициализирующий instance класса для рвботы с инвайт кодами
    """
    def __init__(self, application) -> None:
        self.application = application    

    async def _ask_for_invite_activation(self, update: Update, context: CallbackContext):
        usr, _ = await user_get_by_update(update)

        await context.bot.send_message(
            usr.telegram_chat_id,
            f"💬 Пожалуйста введите инвайт код, полученный от администратора, либо от менеджера.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="В меню 🥃",
                    callback_data="menu"
                )],
            ])
        )

        return 0

    async def _activate_invite_code(self, update:Update, context: CallbackContext):
        usr, _ = await user_get_by_update(update)
        code = update.message.text.strip()
        code_in_base = Invite.objects.filter(code=code).first()

        if code_in_base:
            if code_in_base.valid:
                try:
                    code_in_base.activator = usr
                    code_in_base.valid = False
                    code_in_base.save()

                    usr.type = code_in_base.invite_type
                    usr.verified_usr = True

                    if code_in_base.invite_type.lower() != "воркер":
                        usr.can_create_tasks = True
                    
                    usr.save()

                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"✅ Вы успешно активировали инвайт код. И добавились в проект <b>{code_in_base.project.name}</b>",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="Продолжить 💡",
                                callback_data="menu"
                            )],
                        ])
                    )

                except Exception as e:
                    await context.bot.send_message(
                        usr.telegram_chat_id,
                        f"🤡 Возникла ошибка во время активации инвайт кода. \n\n💩 <b><u>Ошибка:</u></b> <i>{e}</i>",
                        parse_mode="HTML",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton(
                                text="В меню 🥃",
                                callback_data="menu"
                            )],
                        ])
                    )

                return ConversationHandler.END

            else:
                await context.bot.send_message(
                    usr.telegram_chat_id,
                    f"❗️Введенный вами код уже использован ранее. Попробуйте другой код или свяжитесь с администратором.",
                    parse_mode="HTML",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            text="Поддержка 💅🏽",
                            url="https://t.me/i_vovani"
                        )],
                        [InlineKeyboardButton(
                            text="В меню 🥃",
                            callback_data="menu"
                        )],
                    ])
                )
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"❌ Вы ввели неверный код. Проверьте правильность введенного кода или обратитесь к администратору, который вам его выдал.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="Поддержка 💅🏽",
                        url="https://t.me/i_vovani"
                    )],
                    [InlineKeyboardButton(
                        text="В меню 🥃",
                        callback_data="menu"
                    )],
                ])
            )

    @check_user_status
    async def _ask_for_type_of_invite_code(update: Update, context: CallbackContext):
        usr, _ = await user_get_by_update(update)

        if usr.invite_code_limits == 0:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🥲 <b>{usr.username}</b>, к сожалению, у вас больше не осталось возможностей создавать инвайт коды.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🥃",
                        callback_data="menu"
                    )],
                ])
            )

            return ConversationHandler.END

        if usr.type.lower() == "админ":
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Админ 🍊",
                    callback_data="choose_admin",
                )],
                [InlineKeyboardButton(
                    text="Манагер 🍒",
                    callback_data="choose_manager",
                )],
                [InlineKeyboardButton(
                    text="Воркер 🧅",
                    callback_data="choose_worker",
                )],
                [InlineKeyboardButton(
                    text="В меню 🥃",
                    callback_data="menu"
                )],
            ])

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🥂 Выберите тип инвайт кода для пользователя.",
                parse_mode="HTML",
                reply_markup=markup
            )

            return 0
        
        elif usr.type.lower() == "манагер":
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    text="Манагер 🍒",
                    callback_data="choose_manager",
                )],
                [InlineKeyboardButton(
                    text="Воркер 🧅",
                    callback_data="choose_worker",
                )],
                [InlineKeyboardButton(
                    text="В меню 🥃",
                    callback_data="menu"
                )],
            ])

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🥂 Выберите тип инвайт кода для пользователя.",
                parse_mode="HTML",
                reply_markup=markup
            )

            return 0
        
        else:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"⛔️ <b>{usr.username}</b>, у вас нет прав для создания кода, для этого необходим статус <i>Админ</i> или <i>Манагер</i>\n\n<b><u>Ваш статус</u></b>: <i>{usr.type}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🥃",
                        callback_data="menu"
                    )],
                ])
            )

        return ConversationHandler.END

    @check_user_status
    async def _ask_for_project_to_invite(update: Update, context: CallbackContext):
        usr, _ = await user_get_by_update(update)
        context.user_data["invite_type"] = {"manager":"Манагер", "admin":"Админ", "worker":"Воркер"}[update.callback_query.data.split("_")[-1]]

        markup = []
        if usr.type.lower() == "админ":
            projects = Project.objects.filter(creator=usr).all()
        else:
            projects = Project.objects.filter(users__in=[usr]).all()

        if len(projects) == 0:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤡 У вас нет ни одного проекта, куда можно добавить людей. Создайте проект в главном меню и попробуйте снова.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🥃",
                        callback_data="menu"
                    )],
                ])
            )

            return ConversationHandler.END

        for project in projects:
            markup.append([InlineKeyboardButton(text=project.name, callback_data=f"project_choose_{project.id}")])
        markup.append([InlineKeyboardButton(text="В меню 🥃", callback_data="menu")])

        await context.bot.send_message(
                usr.telegram_chat_id,
                f"👽 Выберите проект, куда хотите добавить нового пользователя.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(markup)
            )
        
        return 1

    @check_user_status
    async def _create_invite_code(update: Update, context: CallbackContext):
        usr, _ = await user_get_by_update(update)
        
        code = str(uuid.uuid4())
        invite_type = context.user_data["invite_type"]
        project_to_add_new_worker = Project.objects.get(pk=int(update.callback_query.data.split("_")[-1]))

        try:
            Invite(
                code=code,
                creator=usr,
                invite_type=invite_type,
                project=project_to_add_new_worker
            ).save()

            usr.invite_code_limits -= 1
            usr.save()

            await context.bot.send_message(
                usr.telegram_chat_id,
                f"😻 Вы успешно создали инвайн код с типом <b>{invite_type}</b> для проекта <b>{project_to_add_new_worker.name}</b>. Ваш код:\n\n<code>{code}</code>\n\nНажмите на него, чтобы скопировать, а затем отправьте его человеку, которого хотите добавить в проект.\n\nВы можете создать еще <b><u>{usr.invite_code_limits}</u></b> инвайт кодов.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🥃",
                        callback_data="menu"
                    )],
                ])
            )

        except Exception as e:
            await context.bot.send_message(
                usr.telegram_chat_id,
                f"🤡 Возникла ошибка во время создания инвайт кода. \n\n💩 <b><u>Ошибка:</u></b> <i>{e}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        text="В меню 🥃",
                        callback_data="menu"
                    )],
                ])
            )

        return ConversationHandler.END

    def register_handlers(self) -> None:
        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_type_of_invite_code, "create_invite_code")],
            states={
                0: [CallbackQueryHandler(self._ask_for_project_to_invite, "^choose_")],
                1: [CallbackQueryHandler(self._create_invite_code, "^project_choose_")]
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

        self.application.add_handler(ConversationHandler(
            entry_points=[CallbackQueryHandler(self._ask_for_invite_activation, "invite_code")],
            states={
                0: [MessageHandler(filters.TEXT, self._activate_invite_code)],
            },
            fallbacks=[CallbackQueryHandler(self._start, "menu"), CommandHandler("start", self._start)]
        ))

class Command(BaseCommand):
    help = "Команда запуска телеграм бота"

    def handle(self, *args, **kwargs):        
        application = Bot().register_handlers()

        InviteCodes(application=application).register_handlers()

        application.run_polling()
        
        
