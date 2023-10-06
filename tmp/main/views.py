import logging

from main.models import *

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


@csrf_exempt
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes((AllowAny,))
def main_render(request):
    """"
        Display root html file
    """
    return render(request, 'root.html') 

@csrf_exempt
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes((AllowAny,))
def history_render(request):
    """
        render getting history page
    """
    if request.method == "GET":
        user_chat_id = request.GET.get("user_chat_id", "")
        logging.info(f"{user_chat_id} in history")

        return render(request, "history/history.html")

@csrf_exempt
@ensure_csrf_cookie
@api_view(["POST"])
@permission_classes((AllowAny,))
def delete_user_operation(request):
    try:
        user_chat_id = int(request.POST.get("user_chat_id", None))
        operation_to_delete_id = int(request.POST.get("operation_id", None))

        usr = CustomUser.objects.filter(telegram_chat_id=user_chat_id)
        operation_to_delete = Operation.objects.filter(id=operation_to_delete_id)

        if usr.exists():
            usr = usr.first()
            if operation_to_delete.exists():
                operation_to_delete = operation_to_delete.first()
                if operation_to_delete.creator == usr:
                    operation_to_delete.delete()
                    
                    return Response(
                        {
                            "text":f"Успех! Запись с id={operation_to_delete_id} удалена."
                        },
                        status=HTTP_200_OK
                    )
                else:
                    return Response(
                        {
                            "text":f"Пользователю с chat_id={user_chat_id} не принадлежит операция с id={operation_to_delete_id}"
                        },
                        status=HTTP_400_BAD_REQUEST
                    )    
            else:
                return Response(
                    {
                        "text":f"Операции с id = {operation_to_delete_id} не существует."
                    },
                    status=HTTP_404_NOT_FOUND
                ) 
            
        else:
            return Response(
                {
                    "text":f"Пользователя с chat_id = {user_chat_id} не существует."
                },
                status=HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return Response(
            {"text":f"Данные переданы некорректно. Попробуйте еще раз.\n{e}"},
            status=HTTP_400_BAD_REQUEST
        )

@csrf_exempt
@ensure_csrf_cookie
@api_view(["POST"])
@permission_classes((AllowAny,))
def get_user_operations(request):
    try:
        user_chat_id = int(request.POST.get("user_chat_id", None))
        start_date = request.POST.get("start_date", None)
        end_date = request.POST.get("end_date", None)
        choosen_table_id = int(request.POST.get("table_id", None))

        if (not start_date) or (not end_date):
           raise Exception("Некоторые данные не переданы.") 

    except Exception as e:
        return Response(
            {"text":f"Данные переданы некорректно. Попробуйте еще раз.\n{e}"},
            status=HTTP_400_BAD_REQUEST
        )
    
    user = CustomUser.objects.filter(telegram_chat_id=user_chat_id)
    if user.exists():
        user = user.first()
        if Table.objects.filter(id=choosen_table_id).exists():
            if Table.objects.get(pk=choosen_table_id) in user.get_tables():
                
                end_list = []
                users_table = Table.objects.get(pk=choosen_table_id)
                
                try:
                    active_table_operations = Operation.objects.filter(
                        date__range=[start_date, end_date],
                        table=users_table
                    ).all().order_by('-date')

                    total_income, total_consumption = 0, 0
                    for operation in active_table_operations:
                        oper = {
                                    "id":operation.id,
                                    "date":".".join(reversed(str(operation.date).split()[0].split("-"))),
                                    "amount":operation.amount,
                                    "type":operation.type,
                                    "description":operation.description,
                                }
                        
                        if operation.category_id:
                            oper["category"] = Category.objects.get(pk=operation.category_id).name
                        else:
                            oper["category"] = "Без категории"

                        if operation.type.lower() == "доход":
                            total_income += operation.amount
                        else:
                            total_consumption += operation.amount

                        end_list.append(oper)

                except Exception as e:
                    return Response(
                        {"text":f"Даты введены некорректно.\n{e}"},
                        status=HTTP_400_BAD_REQUEST
                    )

                return Response(
                    {
                        "text":"Успех!",
                        "operations":end_list,
                        "money_info":{
                            "total_income":total_income,
                            "total_consumption":total_consumption,
                            "total_profit":total_income - total_consumption                            
                        }
                    },
                    status=HTTP_200_OK
                )

            else:
                return Response(
                    {"text":f"Таблица с table_id = {choosen_table_id} не принадлежит юзеру {user.username}"},
                    status=HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"text":f"Таблицы с table_id = {choosen_table_id} не существует."},
                status=HTTP_400_BAD_REQUEST
            )
    
    else:
        return Response(
            {
                "text":f"Пользователя с chat_id = {user_chat_id} не существует."
            },
            status=HTTP_404_NOT_FOUND
        )

@csrf_exempt
@ensure_csrf_cookie
@api_view(["POST"])
@permission_classes((AllowAny,))
def get_user_tables(request):
    try:
        user_chat_id = int(request.POST.get("user_chat_id", None))
    
    except Exception as e:
        return Response(
            {"text":f"Данные переданы некорректно. Попробуйте еще раз.\n{e}"},
            status=HTTP_400_BAD_REQUEST
        )
    
    user = CustomUser.objects.filter(telegram_chat_id=user_chat_id)
    if user.exists():
        end_list = [{"table_id":table.id, "table_name":table.name} for table in user.first().get_tables()]
        
        return Response(
            {
                "text":"Успех!",
                "data":end_list
            },
            status=HTTP_200_OK
        )

    else:
        return Response(
            {
                "text":f"Пользователя с chat_id = {user_chat_id} не существует."
            },
            status=HTTP_404_NOT_FOUND
        )
