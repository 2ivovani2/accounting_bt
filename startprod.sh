#!/bin/sh

docker-compose -f docker-compose.prod.yml exec web python manage.py makemigrations bot_constructor --no-input
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate bot_constructor --no-input
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate --no-input
