import requests
import os

bot_token = os.getenv('APPLIER_BOT_TOKEN')
webhook_url = os.getenv('WEBHOOK_URL')

def set_webhook(token, webhook):
    print(bot_token)

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
    if not bot_token or not webhook_url:
        print("Необходимо установить переменные окружения BOT_TOKEN и WEBHOOK_URL.")
    else:
        set_webhook(bot_token, webhook_url)