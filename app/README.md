# TodoList — демо-приложение для вебинара

Как подготовить приложение для запуска в Яндекс.Облаке:
1. Аутентифицироваться в Container Registry
    ```bash
    yc container registry configure-docker
    ```
1. Создать Container Registry
    ```bash
    yc container registry create --name todo-registry
    ```
1. Собрать docker-образ с тегом v1
    ```bash
    docker build app --tag crappyandex/crp0eidcggtp8t0bfh3s/todo-demo:v1
    ```
1. Собрать docker-образ с тегом v2 (для проверки сценария обновления приложения)
    ```bash
    docker build app --build-arg COLOR_SCHEME=dark --tag cr.yandex/crp0eidcggtp8t0bfh3s/todo-demo:v2
    ```
1. Загрузить docker-образы в Container Registry
    ```bash
    docker push cr.yandex/crp0eidcggtp8t0bfh3s/todo-demo:v1
    docker push cr.yandex/crp0eidcggtp8t0bfh3s/todo-demo:v2
    ```
