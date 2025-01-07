import requests, uuid

# Конфигурация
API_BASE_URL = "http://0.0.0.0:8000"  # Базовый URL вашего API
AUTH_ENDPOINT = "/api-token-auth/"     # Эндпоинт для получения токена
CREATE_PAYMENT_ENDPOINT = "/api/create-payment/"  # Эндпоинт для создания платежа

# Пользовательские данные
USERNAME = "alexander"      # Замените на ваш username
PASSWORD = "sashket2003"      # Замените на ваш password

# Данные для создания платежа
PAYMENT_DATA = {
    "amount": "150.00",          # Сумма платежа
    "description": "Оплата подписки",
    "hash":  str(uuid.uuid4()), 
    "redirect_url": "https://google.com",
    "success_webhook": "https://dripmoney.io"
}

def get_auth_token(username, password):
    """
    Получение токена аутентификации.
    """
    url = f"{API_BASE_URL}{AUTH_ENDPOINT}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()  # Поднимет исключение для 4xx/5xx статусов
        token = response.json().get("token")
        if not token:
            print("Токен не найден в ответе.")
            return None
        return token
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ошибка при получении токена: {http_err}")
        print(f"Ответ сервера: {response.text}")
    except Exception as err:
        print(f"Ошибка при получении токена: {err}")
    return None

def create_payment(token, payment_data):
    """
    Создание нового платежа с использованием токена аутентификации.
    """
    url = f"{API_BASE_URL}{CREATE_PAYMENT_ENDPOINT}"
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json=payment_data)
        response.raise_for_status()
        payment_info = response.json()
        print("Платеж успешно создан:")
        print(payment_info)
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP ошибка при создании платежа: {http_err}")
        print(f"Ответ сервера: {response.text}")
    except Exception as err:
        print(f"Ошибка при создании платежа: {err}")

def main():
    # Шаг 1: Получение токена аутентификации
    print("Получение токена аутентификации...")
    token = get_auth_token(USERNAME, PASSWORD)
    
    if not token:
        print("Не удалось получить токен. Проверьте учетные данные и попробуйте снова.")
        return
    
    print(f"Токен получен: {token}")
    
    # Шаг 2: Создание платежа
    print("Создание платежа...")
    create_payment(token, PAYMENT_DATA)

if __name__ == "__main__":
    main()
