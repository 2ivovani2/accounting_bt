#!/bin/sh

docker-compose exec web python manage.py makemigrations bot_constructor --no-input
docker-compose exec web python manage.py migrate bot_constructor --no-input
docker-compose exec web python manage.py migrate --no-input