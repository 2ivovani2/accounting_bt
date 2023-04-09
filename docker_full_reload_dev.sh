#!/bin/sh

docker-compose exec web python manage.py makemigrations --no-input
docker-compose exec web python manage.py migrate --no-input
