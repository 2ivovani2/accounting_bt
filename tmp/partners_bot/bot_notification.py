import requests, logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def notify_bot_user(bot_token, chat_id, text, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode,
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Проверяет наличие HTTP ошибок
        result = response.json()
        if result.get('ok'):
            logging.info("Сообщение успешно отправлено")
        else:
            logging.error(f"Ошибка при отправке сообщения: {result}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Произошла ошибка: {e}")