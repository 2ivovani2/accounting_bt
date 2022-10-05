from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.shortcuts import render
from django.contrib.auth import login, authenticate, logout
from bot_constructor.models import *

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
@api_view(["POST"])
@permission_classes((AllowAny,))
def auth(request):
    """""
        Function of authentication of the user
        TODO: logging via ton wallet
    """
    username = request.POST.get('username', None)
    password = request.POST.get('password', None)
    ton_wallet = request.POST.get('ton_wallet', None)
    auth_type = request.POST.get('auth_type', None)


    if (username is None) or (password is None) or (ton_wallet is None):
        return Response(
            {
                'text':'Your credentials are invalid. Please check them and try again.'
            },
            status=HTTP_400_BAD_REQUEST
        ) 

    if auth_type.lower() == 'login':
        if CustomUser.objects.filter(ton_wallet=ton_wallet).exists():
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

    elif auth_type.lower() == 'register':
        if CustomUser.objects.filter(ton_wallet=ton_wallet).exists():
            return Response({
                    'text':'Such user already exists.',
                },
                status=HTTP_400_BAD_REQUEST
            )
        
        else:
            user = CustomUser(
                username=username,
                ton_wallet=ton_wallet
            )
            user.set_password(password)
            user.save()

            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                    'text':f'{user.username} was successfully created.',
                    'token':token.key,
                },
                status=HTTP_200_OK
            ) 
    
    else:
        return Response(
            {
                'text':'Auth type is not provided.'
            },
            status=HTTP_500_INTERNAL_SERVER_ERROR
        )

@csrf_exempt
@api_view(["POST"])
@permission_classes((AllowAny,))
def get_user_info(request):
    """
        Function of checking actual token info
    """
    token = request.POST.get('token', None)
    
    if token is None:
        return Response(
            {
                'text':'Your token is invalid.'
            },
            status=HTTP_400_BAD_REQUEST
        )

    if Token.objects.filter(key=token).exists():
        user = Token.objects.filter(key=token).first().user

        return Response(
            user.to_dict(),
            status=HTTP_200_OK
        )
    else:
        return Response(
            {
                'text':'Such token doesn\'t exist.'
            },
            status=HTTP_404_NOT_FOUND
        )