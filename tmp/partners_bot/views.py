import json, requests, re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import handle_update

from partners_bot.models import *

import logging

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, render

from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import AutoAcceptCheque
from .serializers import AutoAcceptChequeSerializer
from django.db import DatabaseError, IntegrityError

from django.db.models import Q
from .serializers import SmsReceiverSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.utils import timezone
from datetime import timedelta

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
async def partners_telegram_webhook(request):
    if request.method == 'POST':
        try:
            update_data = request.body.decode('utf-8')
            await handle_update(update_data)
            return JsonResponse({'status': 'ok'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'invalid json'}, status=400)
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({'status': 'error'}, status=500)
    else:
        return JsonResponse({'status': 'only POST allowed'}, status=405)


class CreatePaymentAPIView(generics.CreateAPIView):
    """
    API для создания платежа. Требует аутентификации.
    """
    serializer_class = AutoAcceptChequeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        try:
            # Проверка данных через сериализатор
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            cheque = serializer.instance
            payment_url = request.build_absolute_uri(f"/payment?hash={cheque.hash}")
            headers = self.get_success_headers(serializer.data)
            return Response({
                "payment_url": payment_url,
                "hash": cheque.hash
            }, status=status.HTTP_201_CREATED, headers=headers)
        
        except ValidationError as ve:
            # Обработка валидационных ошибок
            logger.error(f"Validation error: {ve.detail}")
            return Response({
                "error": "Валидационные ошибки",
                "details": ve.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError as ie:
            # Обработка ошибок целостности базы данных (например, дублирование хэша)
            logger.error(f"Integrity error: {str(ie)}")
            return Response({
                "error": "Ошибка целостности данных",
                "details": "Невозможно создать платеж из-за нарушения уникальности или других ограничений."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except DatabaseError as de:
            # Обработка других ошибок базы данных
            logger.error(f"Database error: {str(de)}")
            return Response({
                "error": "Ошибка базы данных",
                "details": "Произошла ошибка при сохранении данных."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            # Обработка всех остальных исключений
            logger.exception("Unexpected error occurred")
            return Response({
                "error": "Внутренняя ошибка сервера",
                "details": "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SmsReceiverAPIView(APIView):
    """
    API для приема SMS от Android-приложения, извлечения суммы платежа и поиска существующего платежа.
    Если платеж не найден, не создается новый.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = SmsReceiverSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Валидация данных не прошла: {serializer.errors}")
            return Response({
                'status': 'error',
                'message': 'Неверные данные.',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        sender = serializer.validated_data['sender']
        text = serializer.validated_data['text']

        logger.info(f"Получены данные SMS от {sender}: {text}")

        # Извлечение суммы из текста SMS с использованием регулярного выражения
        # Предполагается, что сумма указана перед "RUB", "руб.", "руб" и т.д.
        amount_match = re.search(r'(\d+[.,]?\d*)\s*(?:RUB|руб\.?|RUBL)', text, re.IGNORECASE)
        if not amount_match:
            logger.warning("Сумма не найдена в тексте SMS.")
            return Response({
                'status': 'error',
                'message': 'Сумма не найдена в тексте.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        amount_str = amount_match.group(1).replace(',', '.')
        try:
            amount = Decimal(amount_str).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        except Exception as e:
            logger.error(f"Ошибка при преобразовании суммы: {e}")
            return Response({
                'status': 'error',
                'message': 'Неверный формат суммы.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Извлеченная сумма: {amount} RUB")

        try:
            # Попытка найти существующий платеж с точной суммой, отправителем и is_applied=False
            cheque = AutoAcceptCheque.objects.get(
                Q(amount=amount) & Q(is_applied=False)
            )
            logger.info(f"Найден платеж: {cheque.hash} - {cheque.amount} RUB")
        except AutoAcceptCheque.DoesNotExist:
            # Платеж не найден, не создаем новый
            logger.warning(f"Платеж с суммой {amount} RUB не найден.")
            return Response({
                'status': 'error',
                'message': 'Платеж не найден.'
            }, status=status.HTTP_404_NOT_FOUND)
        except AutoAcceptCheque.MultipleObjectsReturned:
            # Обработка ситуации, когда найдено несколько платежей с одинаковой суммой и отправителем
            cheque = AutoAcceptCheque.objects.filter(
                Q(amount=amount) & Q(is_applied=False)
            ).order_by('-created_at').first()
            logger.warning(f"Найдено несколько платежей с суммой {amount} RUB. Выбран последний: {cheque.hash}")

        # Обновление состояния платежа, если необходимо
        if not cheque.is_applied:
            cheque.is_applied = True
            cheque.save()
            logger.info(f"Платеж {cheque.hash} отмечен как примененный.")

        return Response({
            'status': 'success',
            'cheque_hash': cheque.hash
        }, status=status.HTTP_200_OK)

class PaymentPageView(APIView):
    """
    Представление для отображения страницы оплаты по хэшу.
    Добавляет уникальные копейки к сумме чека и применяет комиссию 8%.
    """
    permission_classes = [AllowAny]  # Разрешаем доступ всем, можно настроить по необходимости

    def get(self, request, *args, **kwargs):
        cheque_hash = request.GET.get('hash')
        if not cheque_hash:
            context = {
                'error': 'Отсутствует параметр хэша чека.'
            }
            return render(request, 'payment_page.html', context)
        
        try:
            cheque = AutoAcceptCheque.objects.get(hash=cheque_hash)
        except AutoAcceptCheque.DoesNotExist:
            context = {
                'error': 'Чек с указанным хэшем не найден.'
            }
            return render(request, 'payment_page.html', context)
        
        if cheque.is_applied:
            context = {
                'cheque': cheque,
                'is_applied': True,
                'show_illustration': False  # Иллюстрация не отображается
            }
            return render(request, 'payment_page.html', context)
        
        # Логика назначения уникальных копеек и добавления комиссии
        try:
            original_amount_whole = cheque.amount.quantize(Decimal('1.'), rounding=ROUND_DOWN)  # Целая часть суммы
            # Перебираем копейки от 0.01 до 0.99
            unique_amount_found = False
            for kopeck in range(1, 100):
                added_kopeck = Decimal(kopeck) / Decimal('100')  # Преобразуем в десятичную дробь, например, 0.01
                tentative_amount = original_amount_whole + added_kopeck
                
                # Проверяем, существует ли уже платеж с такой суммой и is_applied=False
                if not AutoAcceptCheque.objects.filter(amount=tentative_amount, is_applied=False).exists():
                    # Добавляем комиссию 8%
                    final_amount = (tentative_amount * Decimal('1.08')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    # Обновляем чек
                    cheque.amount = final_amount
                    cheque.save()
                    
                    logger.info(f"Платеж {cheque.hash} обновлен: сумма {final_amount} RUB (оригинальная сумма {tentative_amount} RUB)")
                    unique_amount_found = True
                    break  # Выходим из цикла, так как уникальная сумма найдена
            
            if not unique_amount_found:
                logger.error(f"Не удалось назначить уникальные копейки для платежа {cheque.hash}")
                context = {
                    'error': 'Не удалось назначить уникальные копейки для суммы чека. Пожалуйста, попробуйте позже.'
                }
                return render(request, 'payment_page.html', context)
        
        except Exception as e:
            logger.exception(f"Ошибка при назначении копеек или добавлении комиссии: {e}")
            context = {
                'error': 'Произошла ошибка при обработке платежа.'
            }
            return render(request, 'payment_page.html', context)
        
        # Поиск свободного процессора
        free_processor = Processor.objects.filter(insurance_deposit__gte=cheque.amount)
        if free_processor.exists():
            free_reks = Reks.objects.filter(reks_owner=free_processor.first(), is_archived=False)
            if free_reks.exists():
                cheque.reks = free_reks.first()
                cheque.save()
        
        if not cheque.reks:
            context = {
                'cheque': cheque,
                'missing_reks': True,
                'show_illustration': False  # Иллюстрация не отображается
            }
            return render(request, 'payment_page.html', context)
        
        # Вычисляем конечное время таймера (created_at + 10 минут)
        end_time = cheque.created_at + timedelta(minutes=10)
        current_time = timezone.now()

        # Проверяем, не истекло ли время
        if current_time >= end_time:
            # Если время истекло, передаем флаг timer_expired
            context = {
                'cheque': cheque,
                'timer_expired': True,
                'show_illustration': False  # Иллюстрация не отображается
            }
            return render(request, 'payment_page.html', context)
        
        # Передаем конечное время в шаблон в формате UNIX timestamp
        context = {
            'cheque': cheque,
            'is_applied': False,
            'end_time': int(end_time.timestamp()),
            'show_illustration': True  # Иллюстрация отображается
        }
        return render(request, 'payment_page.html', context)

class CheckChequeStatusView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        try:
            cheque_hash = request.POST.get('hash')
            if not cheque_hash:
                return Response({'success': False, 'error': 'Отсутствует хэш чека.'}, status=status.HTTP_400_BAD_REQUEST)

            cheque = get_object_or_404(AutoAcceptCheque, hash=cheque_hash)

            if cheque.is_applied:
                # Отправка webhook с сервера
                webhook_url = cheque.success_webhook
                webhook_data = {'cheque_hash': cheque_hash}
                # try:
                #     webhook_response = requests.post(webhook_url, data=webhook_data)
                #     webhook_response.raise_for_status()
                # except requests.RequestException as e:
                #     return Response({'success': False, 'error': f'Ошибка webhook: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                return Response({'success': True, 'is_applied': True}, status=status.HTTP_200_OK)
            else:
                return Response({'success': True, 'is_applied': False}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentSuccessView(APIView):
    """
    Представление для страницы успешной оплаты.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return render(request, 'payment_success.html')