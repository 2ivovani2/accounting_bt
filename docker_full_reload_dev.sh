#!/bin/sh

docker-compose exec web python manage.py makemigrations bot_constructor --no-input
docker-compose exec web python manage.py migrate bot_constructor --no-input
docker-compose exec web python manage.py migrate --no-input
docker-compose exec web python manage.py shell -c "from bbc.bot_constructor.models import CustomUser; CustomUser.objects.create_superuser('alexander', 'admin@example.com', '1234567890')"