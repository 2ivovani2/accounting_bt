from django.urls import path
import bot_constructor.views as views

urlpatterns = [
    path('auth', views.auth),
    path('get_user_info', views.get_user_info),
    path('create_bot', views.create_bot),
    path('stop_bot', views.stop_bot),
    path('start_bot', views.start_bot),
]

