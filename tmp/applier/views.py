import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import handle_update

@csrf_exempt
async def client_telegram_webhook(request):
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
