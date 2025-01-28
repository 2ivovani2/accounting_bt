import json, requests, re
import logging, os

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from datetime import timedelta

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token


from django.db import DatabaseError, IntegrityError
from django.db.models import Q

from partners_bot.models import Processor, Reks  # если у вас так называются модели
from .models import AutoAcceptCheque
from .serializers import AutoAcceptChequeSerializer, SmsReceiverSerializer, DeviceTokenSerializer
from .tasks import handle_update
from .bot_notification import notify_bot_user

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


@csrf_exempt
@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes((permissions.AllowAny,))
def main_render(request):
    """
    Отображение root.html
    """
    return render(request, 'root.html')


@csrf_exempt
async def partners_telegram_webhook(request):
    """
    Async-вебхук для Telegram
    """
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
    API для создания платежа
    """
    serializer_class = AutoAcceptChequeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    def create(self, request, *args, **kwargs):
        try:
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
            logger.error(f"Validation error: {ve.detail}")
            return Response({
                "error": "Валидационные ошибки",
                "details": ve.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as ie:
            logger.error(f"Integrity error: {str(ie)}")
            return Response({
                "error": "Ошибка целостности данных",
                "details": "Невозможно создать платеж из-за нарушения уникальности или других ограничений."
            }, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as de:
            logger.error(f"Database error: {str(de)}")
            return Response({
                "error": "Ошибка базы данных",
                "details": "Произошла ошибка при сохранении данных."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("Unexpected error occurred")
            return Response({
                "error": "Внутренняя ошибка сервера",
                "details": "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SmsReceiverAPIView(APIView):
    """
    API для приема SMS от Android-приложения, извлечения суммы платежа и поиска существующего платежа.
    """
    permission_classes = [permissions.AllowAny]

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

        # Извлечение суммы из текста
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
            # Пытаемся найти соответствующий чек по сумме

            cheque = AutoAcceptCheque.objects.get(
                Q(amount=amount) & Q(is_applied=False) & Q(is_denied=False)
            )
            logger.info(f"Найден платеж: {cheque.hash} - {cheque.amount} RUB")
        except AutoAcceptCheque.DoesNotExist:
            logger.warning(f"Платеж с суммой {amount} RUB не найден.")
            return Response({
                'status': 'error',
                'message': 'Платеж не найден.'
            }, status=status.HTTP_404_NOT_FOUND)
        except AutoAcceptCheque.MultipleObjectsReturned:
            cheque = AutoAcceptCheque.objects.filter(
                Q(amount=amount) & Q(is_applied=False)
            ).order_by('-created_at').first()
            logger.warning(f"Найдено несколько платежей. Выбран последний: {cheque.hash}")

        # Обновление состояния платежа
        if not cheque.is_applied:
            cheque.is_applied = True
            cheque.save()

            usr = cheque.reks.reks_owner                
            usr.clients_withdraw += cheque.amount
            usr.insurance_deposit -= cheque.amount
            usr.balance += cheque.amount * Decimal(usr.comission * 0.01)
            usr.save()
            
            if usr.insurance_deposit <= 0:
                usr.is_ready_to_get_money = False
                usr.save()
                notify_bot_user(
                    text=f"😔 К сожалению, ваш лимит на принятие чеков истек, вам необходимо вывести сумму <b>{usr.balance / ((100 - usr.comission) * 0.01) - usr.balance}RUB</b> на адрес <pre>{os.environ.get('ACCEPT_INSURANCE_PAYMENTS_ADDRESS')}</pre>\n<blockquote>После оплаты отправьте подтверждение администратору и мы разблокирем ваш профиль.</blockquote>",
                    bot_token=os.environ.get("PROCESSORS_BOT_TOKEN"),
                    chat_id=usr.telegram_chat_id
                )

            notify_bot_user(
                text=f"<b>❤️‍🔥 Новое поступление ❤️‍🔥</b>\n\n· Хэш чека - <pre>{cheque.hash}</pre>\n· Сумма поступления - <b>{round(cheque.amount, 2)}₽</b>\n· Ваша доля - <b>{round(cheque.amount * Decimal(usr.comission * 0.01), 2)}₽</b>",
                bot_token=os.environ.get("PROCESSORS_BOT_TOKEN"),
                chat_id=usr.telegram_chat_id
            )
            logger.info(f"Платеж {cheque.hash} отмечен как примененный.")

        return Response({
            'status': 'success',
            'cheque_hash': cheque.hash
        }, status=status.HTTP_200_OK)


class PaymentPageView(APIView):
    """
    Отображение страницы оплаты по хэшу. 
    Если чек ещё не оплачен/не отклонён — и при этом его сумма целая, 
    то добавляем уникальные копейки + комиссию один раз. 
    Повторные открытия страницы не увеличивают сумму.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        cheque_hash = request.GET.get('hash')
        if not cheque_hash:
            return render(request, 'payment_page.html', {
                'error': 'Отсутствует параметр хэша чека.'
            })

        try:
            cheque = AutoAcceptCheque.objects.get(hash=cheque_hash)
        except AutoAcceptCheque.DoesNotExist:
            return render(request, 'payment_page.html', {
                'error': 'Чек с указанным хэшем не найден.'
            })

        # Если чек уже применён (оплачен)
        if cheque.is_applied:
            context = {
                'cheque': cheque,
                'is_applied': True,
                'show_illustration': False
            }
            return render(request, 'payment_page.html', context)

        # Если чек уже отклонён
        if cheque.is_denied:
            return render(request, 'payment_page.html', {
                'error': 'Чек уже отклонён.'
            })

        # ============ Проверка, нужно ли добавлять копейки/комиссию ============

        # 1) Смотрим целую часть суммы (например, 100.00)
        original_amount_whole = cheque.amount.quantize(Decimal('1.'), rounding=ROUND_DOWN)

        # 2) Если сейчас чек имеет ровно "целую" сумму, значит копейки ещё не добавлялись
        if cheque.amount == original_amount_whole:
            try:
                # Перебираем копейки от 0.01 до 0.99
                unique_amount_found = False
                for kopeck in range(1, 100):
                    added_kopeck = Decimal(kopeck) / Decimal('100')  # 0.01 ... 0.99
                    tentative_amount = original_amount_whole + added_kopeck

                    # Проверяем, не занят ли уже кто-то такой же суммой
                    # (и чек при этом не оплачен, не отклонён)
                    if not AutoAcceptCheque.objects.filter(
                        amount=tentative_amount, is_applied=False, is_denied=False
                    ).exists():
                        # Комиссию берём из env либо по умолчанию 1.08 (8%)
                        commission_rate = Decimal(os.environ.get("AUTO_COMISSION", "1.08"))
                        final_amount = (tentative_amount * commission_rate).quantize(
                            Decimal('0.01'),
                            rounding=ROUND_HALF_UP
                        )

                        # Записываем новую сумму в чек
                        cheque.amount = final_amount
                        cheque.save()
                        unique_amount_found = True
                        break

                if not unique_amount_found:
                    # Если мы не нашли свободных копеек, выдаём ошибку
                    return render(request, 'payment_page.html', {
                        'error': 'Не удалось назначить уникальные копейки. Попробуйте позже.'
                    })

            except Exception as e:
                # Ловим любые ошибки (например, проблемы с БД)
                return render(request, 'payment_page.html', {
                    'error': f'Произошла ошибка при обработке платежа: {e}'
                })

        # ============ Далее проверяем, есть ли реквизиты и не истёк ли таймер ============

        # Ищем реквизиты (пример: ищем процессора, у которого достаточно страхового депозита)
        if not cheque.reks:
            free_processor = Processor.objects.filter(insurance_deposit__gte=cheque.amount).first()
            if free_processor:
                free_reks = Reks.objects.filter(reks_owner=free_processor, is_archived=False).first()
                if free_reks:
                    cheque.reks = free_reks
                    cheque.save()

        if not cheque.reks:
            cheque.is_denied = True
            cheque.save()

            return render(request, 'payment_page.html', {
                'cheque': cheque,
                'missing_reks': True,
                'show_illustration': False
            })

        # Проверяем 10-минутный таймер: если время вышло — отклоняем
        end_time = cheque.created_at + timedelta(minutes=10)
        current_time = timezone.now()
        if current_time >= end_time:
            cheque.is_denied = True
            cheque.save()
            return render(request, 'payment_page.html', {
                'cheque': cheque,
                'timer_expired': True,
                'show_illustration': False
            })

        # Если пока всё нормально: передаём время окончания и рисуем страницу
        context = {
            'cheque': cheque,
            'is_applied': False,
            'end_time': int(end_time.timestamp()),
            'show_illustration': True
        }
        return render(request, 'payment_page.html', context)

class CheckDeviceTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, format=None):
        serializer = DeviceTokenSerializer(data=request.data)
        if serializer.is_valid():
            device_token = serializer.validated_data.get('device_token')
            exists = Processor.objects.filter(device_token=device_token).exists()
            return Response({'exists': exists}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckChequeStatusView(APIView):
    """
    POST-запрос для проверки статуса чека
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        cheque_hash = request.data.get('hash') or request.POST.get('hash')
        if not cheque_hash:
            return Response({'success': False, 'error': 'Отсутствует хэш чека.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cheque = get_object_or_404(AutoAcceptCheque, hash=cheque_hash)

            if cheque.is_applied:
                # Можно вызывать тут webhook, если надо
                webhook_url = cheque.success_webhook
                if webhook_url:
                    requests.post(webhook_url, data={'cheque_hash': cheque_hash})

                return Response({'success': True, 'is_applied': True}, status=status.HTTP_200_OK)
            else:
                return Response({'success': True, 'is_applied': False}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentSuccessView(APIView):
    """
    Страница успешной оплаты
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        redirect_url = request.GET.get('redirect_url', None)
        return render(request, 'payment_success.html', {'redirect_url': redirect_url})

class DocumentationView(APIView):
    """
    Страница успешной оплаты
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        return render(request, 'doc.html')


class DenyChequeView(APIView):
    """
    По POST hash=... выставляет is_denied=True для чека
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        cheque_hash = request.data.get('hash') or request.POST.get('hash')
        if not cheque_hash:
            return Response({'success': False, 'error': 'No hash provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            cheque = AutoAcceptCheque.objects.get(hash=cheque_hash)
            cheque.is_denied = True
            cheque.save()
            return Response({'success': True, 'message': 'Cheque denied'}, status=status.HTTP_200_OK)
        except AutoAcceptCheque.DoesNotExist:
            return Response({'success': False, 'error': 'Cheque not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckTokenView(APIView):
    """
    Проверяет наличие токена (приходит в POST-данных: token=...)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        # Ищем токен либо в request.data (DRF) либо в request.POST (Django)
        token_value = request.data.get('token') or request.POST.get('token')
        if not token_value:
            return Response(
                {'success': False, 'error': 'No token provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, есть ли в базе запись с таким ключом
        token_exists = Token.objects.filter(key=token_value).exists()

        return Response(
            {'success': True, 'token_exists': token_exists}, 
            status=status.HTTP_200_OK
        )