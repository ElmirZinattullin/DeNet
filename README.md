# DeNet

Запуск СУБД Postgresql
```shell
docker run --name denet-db -e POSTGRES_USER=denet -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=denet -p 5431:5432 -d postgres
```