from django.urls import path

import bot_constructor.views as views

urlpatterns = [
    path('auth', views.auth),
    path('get_user_info', views.get_user_info)
]