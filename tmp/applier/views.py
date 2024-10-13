# bot/views.py
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from .tasks import handle_update
from .tasks import application

@csrf_exempt
def telegram_webhook(request):
    if request.method == 'POST':
        try:
            update = request.body.decode('utf-8')
            handle_update.delay(update)
            return HttpResponse({'status': 'ok'}, status=200)

        except json.JSONDecodeError:
            return HttpResponse({'status': 'invalid json'}, status=400)
    else:
        return HttpResponse({'status': 'only POST allowed'}, status=405)