"""tmp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from main.views import main_render
from applier.views import client_telegram_webhook
from partners_bot.views import partners_telegram_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main_render),
    path('client_webhook', client_telegram_webhook, name='client_telegram_webhook'),
    path('processors_webhook', partners_telegram_webhook, name='partners_telegram_webhook'),
]

admin.site.site_header = "Drip Money"
admin.site.index_title = "Админка Drip Money 🥰"