# hw2 - logs in clickhouse  

## infrastructure
5 vm:  
- nginx - lan-net - 192.168.1.4 and white ip
- nat - lan-net - 192.168.1.3 and white ip

- back1 - lan-net - 192.168.1.5
- back2 - lan-net - 192.168.1.6

- clickhouse - lan-net - 192.168.1.7  

subnet:
- lan-net - 192.168.1.0/24

forwarding table:  
```
destination_prefix = "0.0.0.0/0"
next_hop_address   = "192.168.1.3"
```

terraform builds everything.  

## deployment
we implement `docker-compose.yml` with terraform COI instances: 
```
resource "yandex_compute_instance" "back1" {
  name     = "hw2-back1"
  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.container-optimized-image.id
    }
  }
  network_interface {
    subnet_id  = yandex_vpc_subnet.lan-net.id
    nat        = false
    ip_address = "192.168.1.5"
  }
  resources {...}
  metadata = {
    docker-compose = file("back/docker-compose.prod.yml")
    user-data      = file("cloud-config.yml")
  }
}
```
this way we automatically deply:  
- **nginx** with custom config that writes into the container,
- 2 **back instances** with instantly running application,
- **clickhouse** server with instantly created scheme.  

docker image: 
https://git.miem.hse.ru/asshadrunov/hw2-cloud/container_registry
### sources:
- use docker compose with YC COI: https://cloud.yandex.com/en-ru/docs/cos/concepts/coi-specifications#compose-spec  
- to use in specification.yaml the Docker Compose specification, specify the `docker-compose` key instead of the `docker-container-declaration` key. [here](https://cloud.yandex.com/en-ru/docs/cos/solutions/ig-create)
- yandex_compute_instance reference: https://registry.terraform.io/providers/yandex-cloud/yandex/latest/docs/resources/compute_instance

## application

1. accept post request with logs, check format of each of them, write valid log_entries to the file. invalid entries go to error.txt
1. every $t$ seconds clear file and append every log_entry in csv format to StringIO with name of the table
1. execute query on the first StringIO, wait a sec, continue with the rest StringIOs
1. scheduler waits a second


## API

Предполагается, что необходимые таблицы уже созданы в ClickHouse, в который ходит сервис. 

### `GET /healthcheck`

Отвечает `200 OK`, когда запущен. Используется для балансировщика в автоскейлере, который проверяет живые сервисы. 

### `GET /show_create_table?table_name=some_table`

Ходит в ClickHouse и делает `SHOW CREATE TABLE "some_table"`, чтобы пользователь мог проверить актуальную схему таблицы.

```
$ curl 'http://84.201.154.209/show_create_table?table_name=kek'

CREATE TABLE default.kek
(
    `a` Int32,
    `b` String
)
ENGINE = MergeTree
PRIMARY KEY a
ORDER BY a
SETTINGS index_granularity = 8192
```

### `POST /write_log`
Принимает логи для записи в формате, описанном ниже. Проверяет примитивную валидность формата, записывает в файл с очередью на отправку `data.txt`.

Пример записи логов:

```
$ curl 'http://84.201.154.209/write_log' \
                        -d '[{"table_name": "kek", "rows": [{"a":1, "b": "some new row"}, {"a": 2}], "format": "json"}, {"table_name": "kek", "rows": [[1, "row from list"]], "format": "list"}]' -v

> POST /write_log HTTP/1.1
> Host: 84.201.154.209
> User-Agent: curl/7.81.0
> Accept: */*
> Content-Length: 164
> Content-Type: application/x-www-form-urlencoded
> 
* Mark bundle as not supporting multiuse
< HTTP/1.1 200 OK
< Server: nginx/1.21.6
< Date: Tue, 01 Feb 2022 10:30:07 GMT
< Content-Type: application/json
< Content-Length: 3
< Connection: keep-alive
< 
* Connection #0 to host 84.201.154.209 left intact
200
```

Возвращается 200, если приложение приняло логи и передаст их в clickhouse.  

Тело запроса в читаемом фромате:
```json
[
  {
    "table_name": "kek",
    "rows": [
      {"a": 1, "b": "some new row"},
      {"a": 2}
    ],
    "format": "json"
  },
  {
    "table_name": "kek",
    "rows": [
      [1, "row from list"]
    ],
    "format": "list"
  }
]
```

### `GET /undelivered_internal`
показывает список недоставленных логов на инстансе. не доступен снаружи  
### `GET /undelivered`

```
curl 'http://84.201.154.209/undelivered'

from 1 node: 
"10","undelivered"
"10","undelivered"
"10","undelivered"
from 2 node: 
"10","undelivered"
"10","undelivered"
"10","undelivered"
```
показывает общий список недоставленных логов на обоих инстансах. иногда не доступен, когда происходит обновление списка  
### `GET /logs`
показывает логи

## Как запустить локально
```
python back/run_debug.py
```

## Как собрать локально
```
cd back
docker build -t registry.miem.hse.ru/asshadrunov/hw2-cloud .
docker push registry.miem.hse.ru/asshadrunov/hw2-cloud
```

## Как запустить в YC
```
terraform destroy -auto-approve
terraform apply -auto-approve
```

## Подключиться по ssh
```
ssh -o StrictHostKeyChecking=no -J <nat ip> 192.168.1.5  # back1
ssh -o StrictHostKeyChecking=no -J <nat ip> 192.168.1.6  # back2
ssh -o StrictHostKeyChecking=no -J <nat ip> 192.168.1.7  # db
```

docker команды:
```
sudo docker exec -it back bash

sudo docker run -it --rm yandex/clickhouse-client --host 192.168.1.7 --port 9000
aa121ecaa456 :) select * from kek

SELECT *
FROM kek

Query id: 91f72d9a-46a5-4ca1-99e7-dc1b7407bbc8

┌──a─┬─b───────────┐
│ 10 │ undelivered │
│ 10 │ undelivered │
│ 10 │ undelivered │
└────┴─────────────┘

28 rows in set. Elapsed: 0.017 sec. 

```

## Пример работы
произошёл рестарт ноды, приложение подобрало строки из текущей очереди `data_rows` и обработало. так как доставить в базу не получилось, добавили в очередь `undelivered`. далее включили базу и логи были отправлены. 
```
INFO:uvicorn.error:Started server process [1]
INFO:uvicorn.error:Waiting for application startup.
INFO:apscheduler.scheduler:Adding job tentatively -- it will be properly scheduled when the scheduler starts
INFO:apscheduler.scheduler:Added job "send_to_db" to job store "default"
INFO:apscheduler.scheduler:Scheduler started
INFO:uvicorn.error:Application startup complete.
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:root:write_log accessed: 0 undelivered_rows processed
INFO:root:write_log accessed: 25 data_rows processed
INFO:root:send_csv - sending to db: ('kek', '"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n"6","row2"\r\n')
ERROR:root:send_csv undelivered: ()
INFO:root:undelivered accessed
INFO:root:undelivered internal accessed
INFO:root:write_log accessed: 25 undelivered_rows processed
INFO:root:write_log accessed: 0 data_rows processed
INFO:root:send_csv - sending to db: ('kek', '"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n')
ERROR:root:send_csv undelivered: ()
INFO:root:write_log accessed: 25 undelivered_rows processed
INFO:root:write_log accessed: 0 data_rows processed
INFO:root:send_csv - sending to db: ('kek', '"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n')

INFO:root:write_log accessed: 25 undelivered_rows processed
INFO:root:write_log accessed: 0 data_rows processed
INFO:root:send_csv - sending to db: ('kek', '"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n"6","row2"\n')
WARNING:root:200
INFO:root:send_csv sent to db
INFO:root:logs accessed
```

# Compliance 
- *она должна переживать перезапуск ноды над тем же диском*  

работает, так как логи лежат в файле на диске и диск не ротируется

- *она должна ходить в ClickHouse не чаще раза в секунду, а не на каждый запрос `write_log`*  

ходит тогда, когда запускается scheduler, то есть раз в 1 или 2 секунды  

- *все принятые логи должны быть доставлены до ClickHouse (возможно несколько раз из-за сетевых проблем), принятые в данном случае означает, что мы получили логи в запросе, записали их на диск, после чего ответили на запрос 200 OK, что является гарантией того, что мы доставим этот лог до СУБД. Для вставки неотправленных логов в момент выключения машины можно воспользоваться [shutdown event в fastapi](https://fastapi.tiangolo.com/advanced/events/#shutdown-event).*

недоставленные логи лежат в отдельном файле и пытаются быть доставленными, иначе остаются в файле
- *в текущей реализации пользователь сразу узнает, удалось ли записать логи в табличку или нет, при асинхронной отправке это свойство будет утеряно, но нужен какой-то асинхронный способ проверки доставки, придумайте сами (это может локальный персистентный список с неуспешными запросами, например)*  

можно посмотреть файл из предыдущего пункта

# итог
- **+4 балла** Деплой инфраструктуры (nginx + 2 бэкенда с logbroker + clickhouse + NAT)
- **+2 балла** Сеть настроена правильно, то есть только у двух машин публичный адрес — nginx и NAT-инстанс.
- **+2 балла** Реализована персистентная буферизация в логброкере
- **+2 балла** Для деплоя инфраструктуры использовался Terraform
- (бонус) **+1 балл** все сервисы стартуют сами с помощью терраформа, вся конфигурация может быть развёрнута с помощью `terraform apply`