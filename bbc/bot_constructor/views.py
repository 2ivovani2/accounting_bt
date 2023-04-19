from os import stat
import time
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.shortcuts import render
from django.contrib.auth import authenticate

from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.status import (
    HTTP_200_OK,
    
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    
    HTTP_500_INTERNAL_SERVER_ERROR
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

from bot_constructor.models import *
import threading

class StoppableBotThread(threading.Thread):
    """
        Thread class with a stop() method. 
        The thread itself has to check
        regularly for the stopped() condition.
    """

    def __init__(self, *args, **kwargs):
        super(StoppableBotThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

@csrf_exempt
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes((AllowAny,))
def vue(request):
    """"
        Display vue main file
    """
    return render(request, 'root.html') 


@csrf_exempt
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes((AllowAny,))
def payment_tnx(request):
    """
        Display tnx payment
        TODO переписать
      """
    logger.info(request.POST, request.GET)
    return redirect(f"https://t.me/i_vovani")

@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def auth(request):
    """""
        Function of authentication of the user
        TODO: registration of new admins
    """
    username = request.POST.get('username', None).strip()
    password = request.POST.get('password', None).strip()
    auth_type = request.POST.get('auth_type', '').strip()


    if (username is None) or (password is None):
        return Response(
            {
                'text':'Your credentials are invalid. Please check them and try again.'
            },
            status=HTTP_400_BAD_REQUEST
        ) 

    if auth_type.lower() == 'login':
        if CustomUser.objects.filter(username=username).exists():
            user = authenticate(username=username, password=password)
            
            if not user:
                return Response(
                    {'text':'Your credentials are invalid. Please check them and try again'},
                    status=HTTP_403_FORBIDDEN
                )
            
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                    'text':f'{user.username} was successfully authenticated.',
                    'token':token.key,
                },
                status=HTTP_200_OK
            ) 

        else:
            return Response({
                    'text':'Such user does not exist.',
                },
                status=HTTP_400_BAD_REQUEST
            ) 


@csrf_exempt
@api_view(["POST"])
def get_user_info(request):
    """
        Function of checking actual token info
    """
    token = request.POST.get('token', None).strip()
    
    if token is None:
        return Response(
            {
                'text':'Your token is invalid.'
            },
            status=HTTP_400_BAD_REQUEST
        )

    if Token.objects.filter(key=token).exists():
        user = Token.objects.filter(key=token).first().user

        bots = Bot.objects.filter(owner=user).all()
        bots_info = [bot.to_dict() for bot in bots]

        return Response(
            {
                'web_user_info':user.to_dict(),
                'web_user_bots_info':bots_info,
            },
            status=HTTP_200_OK
        )
    else:
        return Response(
            {
                'text':'Such token doesn\'t exist.'
            },
            status=HTTP_404_NOT_FOUND
        )


@csrf_exempt
@api_view(['POST'])
def stop_bot(request):
    """
        Function that gives you ability to kill a thread with running bot by name
    """

    bot_token = request.POST.get('bot_token', None)

    if bot_token is None:
        return Response(
            {
                'text':'Token of bot\'s thread is incorrect. Connect with support.'
            },
            status=HTTP_400_BAD_REQUEST
        )
    else:
        bot_token = bot_token.strip()


    if Bot.objects.filter(token=bot_token, owner=request.user).exists():
        threads = threading.enumerate()
        for index in range(len(threads)): 
            if threads[index].name.strip() == bot_token:
                bot_thread = threads[index]
                threads[index].stop()
                threads[index + 1].stop()

    else:
        return Response(
            {
                'text':'Such bot doesn\'t exist or you don\'t have access to it.'
            },
            status=HTTP_400_BAD_REQUEST
        )

    if bot_thread.stopped():
        b = Bot.objects.filter(token=bot_token, owner=request.user).first()
        b.is_active = False
        b.save()

        return Response(
            {
                'text':'Your bot is successfully stopped.'
            },
            status=HTTP_200_OK
        )
    else:
        return Response(
            {
                'text':'Some errors occured. Connect support please.'
            },
            status=HTTP_500_INTERNAL_SERVER_ERROR
        )
    

@csrf_exempt
@api_view(["POST"])
def create_bot(request):
    """
        Function which creates bot and host it
    """
    
    bot_token = request.POST.get('bot_token', None)
    bot_name = request.POST.get('bot_name', None)


    if bot_token is None:
        return Response(
            {
                'text':'Your token is invalid.'
            },
            status=HTTP_400_BAD_REQUEST
        )
    else:
        bot_token = bot_token.strip()
        
    user = request.user
    
    if Bot.objects.filter(token=bot_token).exists():
        return Response(
            {
                'text':'Bot with such token already exists. Try another token.'
            },
            status=HTTP_400_BAD_REQUEST
        )
    
    try:
        new_bot = Bot(
            token=bot_token,
            name=bot_name,
            owner=user,
        )

        name = new_bot.create_telegram_instance()
        new_bot.telegram_name = name

        try:
            daemon = StoppableBotThread(
                target=new_bot.start_telegram_bot_instance,
                daemon=True, 
                name=f"{bot_token}"
            )
            daemon.start()
        except:
            return Response(
                {
                    'text':f'Bot with this token already hosted.'
                },
                status=HTTP_500_INTERNAL_SERVER_ERROR
            )

        new_bot.is_active = True

    except Exception as e:
        return Response(
            {
                'text':f'Your bot is not hosted. Try again later. Error {e}'
            },
            status=HTTP_500_INTERNAL_SERVER_ERROR
        )

    new_bot.save()
    

    return Response(
        {
            'text':f'Your bot was successfully hosted.'
        },
        status=HTTP_200_OK
    )
   

@csrf_exempt
@api_view(["POST"])
def start_bot(request):
    """
        Function that gives you ability to start a thread with running bot by name
    """

    bot_token = request.POST.get('bot_token', None).strip()

    if bot_token is None:
        return Response(
            {
                'text':'Token of bot\'s thread is incorrect. Connect with support.'
            },
            status=HTTP_400_BAD_REQUEST
        )

    if Bot.objects.filter(token=bot_token, owner=request.user).exists():
        try:
            b = Bot.objects.filter(token=bot_token, owner=request.user).first()
            b.create_telegram_instance()
            
            try:
                daemon = StoppableBotThread(
                    target=b.start_telegram_bot_instance,
                    daemon=True, 
                    name=f"{bot_token}"
                )
                daemon.start()
            except:
                return Response(
                    {
                        'text':f'Bot with this token already hosted.'
                    },
                    status=HTTP_500_INTERNAL_SERVER_ERROR
                )

            
            b.is_active = True
            b.save()
            return Response(
                            {
                                'text':'Your bot is successfully started.'
                            },
                            status=HTTP_200_OK
                        )
        except:
                return Response(
                                {
                                    'text':'Some errors occured. Connect support please.'
                                },
                                status=HTTP_500_INTERNAL_SERVER_ERROR
                        )
    else:
        return Response(
            {
                'text':'Such bot doesn\'t exist or you don\'t have access to it.'
            },
            status=HTTP_400_BAD_REQUEST
        )
    
