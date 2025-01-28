
from django.urls import path
from .views import *

urlpatterns = [
    path('', main_render, name='main-render'),  # Корневой маршрут для отображения root.html
    path('processors_webhook', partners_telegram_webhook, name='partners_telegram_webhook'),
    path('api/create-payment/', CreatePaymentAPIView.as_view(), name='create-payment'),
    path('payment/', PaymentPageView.as_view(), name='payment-page'),
    path('payment/check_status/', CheckChequeStatusView.as_view(), name='check_cheque_status'),
    path('payment/success/', PaymentSuccessView.as_view(), name='payment_success'),
    path('api/sms_receiver/', SmsReceiverAPIView.as_view(), name='sms_receiver'),
    path('deny-cheque/', DenyChequeView.as_view(), name='deny_cheque'),
    path('check-token/', CheckTokenView.as_view(), name='check_token'),
    path('check-device-token/', CheckDeviceTokenView.as_view(), name='check_device_token'),
    path('doc/', DocumentationView.as_view(), name='documentation'),
]