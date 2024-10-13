FROM python:3.9-slim

# Установите необходимые зависимости
RUN pip install requests

# Скопируйте скрипт для обновления вебхука в контейнер
COPY update_webhook.py /app/update_webhook.py

# Выполните скрипт при запуске контейнера
CMD ["python", "/app/update_webhook.py"]