import requests
import os

client_bot_token = os.getenv('APPLIER_BOT_TOKEN')
client_webhook_url = os.getenv('CLIENT_WEBHOOK_URL')

partners_bot_token = os.getenv('PROCESSORS_BOT_TOKEN')
partners_webhook_url = os.getenv('PARTNERS_WEBHOOK_URL')

def set_webhook(token, webhook):
    url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    response = requests.post(url, data={'url': webhook})

    if response.status_code == 200:
        print(response.text)
        print("Webhook удален успешно.")
    else:
        print(f"Ошибка при удалении вебхука: {response.text}")

    url = f"https://api.telegram.org/bot{token}/setWebhook"
    response = requests.post(url, data={'url': webhook})
    
    if response.status_code == 200:
        print(response.text)
        print("Webhook установлен успешно.")
    else:
        print(f"Ошибка при установке вебхука: {response.text}")

if __name__ == "__main__":
    if not client_bot_token or not partners_bot_token:
        print("Необходимо установить переменные окружения BOT_TOKEN для двух ботов")
    elif not client_webhook_url or not partners_webhook_url:
        print("Необходимо установить переменные окружения WEBHOOK_URL для двух ботов")
    else:
        set_webhook(client_bot_token, client_webhook_url)
        set_webhook(partners_bot_token, partners_webhook_url)