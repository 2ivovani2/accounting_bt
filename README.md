# ООО Обнал 👶🏽
This telegram system is multifunctional.<br> It will have an partner programm<br> and a bot constructor for various promotions
## Docker Development 🐳👁
You have to change all the credentials in file `.env.dev` on your own and then run these commands:
```shell
$: docker-compose up -d --build
```
Then your development server will be on http://127.0.0.1:8000 <br><br>
If you want to stop the containers run
```shell
$: docker-compose down -v
```

## Docker Production 🐳💥
You have to change all the credentials in file `.env.prod` and `.env.prod.db` on your own and then run these commands:
```shell
$: docker-compose -f docker-compose.prod.yml up -d --build 
```
Then your prod will be on http://127.0.0.1:1337 on local host becuse of the `nginx`, but if you start it on prod server, just enter it's `IP` or `Domain name` and you'll see the same result.<br><br>
If you want to stop the containers run
```shell
$: docker-compose -f docker-compose.prod.yml down -v
```
