from django.urls import path
import bot_constructor.views as views

urlpatterns = [
    path('auth', views.auth),
    path('create_bot', views.create_bot),
    path('stop_bot', views.stop_bot),
    path('start_bot', views.start_bot),
    path('confirm_payment', views.payment_tnx)
]

