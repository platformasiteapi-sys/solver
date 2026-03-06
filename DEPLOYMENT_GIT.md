# Деплой TexasSolver API через GitHub и Timeweb Cloud

Этот метод деплоя — самый чистый и надежный. Мы используем приватный репозиторий GitHub для хранения кода и встроенный в Timeweb Cloud-init для автоматического развертывания.

## Шаг 1: Подготовка Репозитория
1. **Скачай Linux-версию солвера**: Зайди на [официальный GitHub TexasSolver](https://github.com/bupticybee/TexasSolver/releases) и скачай релиз для Linux (рекомендуется `v0.2.0`, так как в `v0.3.3` нет публичной консольной версии для Linux).
2. Распакуй архив и положи файл `console_solver` **И** папку `resources` внутрь папки твоего проекта по такому пути: `linux_bin/console_solver` и `linux_bin/resources/`. Папка `resources` критически важна для работы солвера. Скрытые файлы вроде `.DS_Store` копировать не нужно.
3. Зарегистрируй новый (желательно **приватный**) репозиторий на GitHub (например, `texassolver-api`).
4. На своем ПК инициализируй папку `d:\Antigravity_projects\m` как git-репозиторий и запуш все файлы (включая папку `linux_bin` с бинарником и ресурсами) в GitHub.

## Шаг 2: Создание токена (Personal Access Token)
Если твой репозиторий приватный, Timeweb не сможет просто так скачать его.
1. Зайди в настройки своего GitHub аккаунта -> **Developer Settings** -> **Personal access tokens** -> **Tokens (classic)**.
2. Нажми **Generate new token (classic)**. Отметь галочку `repo` (Full control of private repositories).
3. Скопируй сгенерированный токен (он начинается с `ghp_...`).

## Шаг 3: Настройка Cloud-init
В папке проекта лежит файл `github-cloud-config.yaml`. Открой его.
Найди строку `git clone...` и замени ее на такую:
`git clone https://<твой_логин>:<твой_токен>@github.com/<твой_логин>/<имя_репозитория>.git /root/texassolver-api`

*Пример: `git clone https://Alex:ghp_123456789abc@github.com/Alex/texassolver-api.git /root/texassolver-api`*

## Шаг 4: Аренда сервера
1. Зайди в панель Timeweb Cloud и нажми **Создать сервер**.
2. Выбери операционную систему **Ubuntu 22.04**.
3. В поле **"Дополнительно" -> "Скрипт при старте" (или Cloud-init)** скопируй весь получившийся у тебя текст из файла `github-cloud-config.yaml`.
4. Нажми **Заказать**.

## Шаг 5: Проверка
Через 3-5 минут после создания сервера, когда скрипт закончит установку Docker'а и сборку образа, API будет доступно.

Проверь его простым PowerShell-запросом (заменив IP на IP твоего сервера):
```powershell
Invoke-RestMethod -Uri "http://<твой-ip-сервера>:80/api/solve" -Method Post -Headers @{"Content-Type"="application/json"} -Body '{"pot": 50.0, "effective_stack": 200.0, "board": "Qs,Jh,2h", "range_ip": "QQ:0.5,JJ:0.75,TT,99,88,77,66,55,44,33,22,AK", "range_oop": "AA,KK,QQ,JJ,TT,99:0.75,88:0.75,77:0.5", "thread_num": 6, "accuracy": 0.5, "max_iteration": 20}'
```
