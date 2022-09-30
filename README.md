# BabyBossesClub Utility 👶🏽
This NFT ecosystem is multifunctional.<br> It will have an NFT marketplace with a built-in analytics system<br> and a bot constructor for various promotions
## Quick start 💥

1. You have to config the `.env` file:
  - Change Django App `SECRET_KEY`, `DEBUG`, `DJANGO_ALLOWED_HOSTS` to yours from `settings.py`
  - Change PostreSQL `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD` constants too on yours

2. Then make sure that you have installed `docker` and `docker-compose`:
```shell
docker --version
```
```shell
docker-compose --version
```

3. If everything is okay you have to change directory where `docker-compose.yml` file locates then make docker build and up the containers
```shell
docker-compose up -d --build
```

