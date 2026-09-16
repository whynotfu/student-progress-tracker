# StudGrade — автоматизированная система учёта успеваемости студентов

Веб-приложение на Flask, реализующее требования технического задания
(`лб1/Техническое задание.docx`): учёт контингента студентов, учебных
планов и журнала успеваемости, а также две расчётные функции:

- количество студентов по заданной форме обучения;
- количество часов и форма отчётности по заданной дисциплине.

Стек согласно п. 4.3.3 ТЗ: **Python 3.12 + Flask 3.1**, СУБД —
**PostgreSQL 16.15** (см. «Настройка базы данных» ниже). Это
**скриптовый язык**, поэтому по заданию лр2 приложение не нужно
"собирать" — на стенде запускается прототип напрямую (`python wsgi.py`
или через `gunicorn`).

## Настройка базы данных

По умолчанию (без переменной окружения `DATABASE_URL`) приложение
использует SQLite — это удобно для быстрого локального запуска, но не
соответствует п. 4.3.1/4.3.3 ТЗ, где зафиксирована PostgreSQL 16.15.
Для стендов лр2 (test/stage/prod) поднимите PostgreSQL и укажите
строку подключения:

```bash
sudo apt install -y postgresql
sudo -u postgres psql -c "CREATE DATABASE studgrade;"
sudo -u postgres psql -c "CREATE USER studgrade WITH PASSWORD 'studgrade';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE studgrade TO studgrade;"

export DATABASE_URL="postgresql://studgrade:studgrade@localhost:5432/studgrade"
```

Драйвер `psycopg2-binary` уже входит в `requirements.txt`.

### Резервное копирование

П. 4.1.9/4.2.1 ТЗ требуют возможности резервного копирования данных
средствами СУБД. Для PostgreSQL это штатный `pg_dump`/`pg_restore`:

```bash
pg_dump -U studgrade -h localhost studgrade > studgrade_$(date +%F).sql
# восстановление:
psql -U studgrade -h localhost studgrade < studgrade_2026-09-16.sql
```

Для автоматического (периодического) копирования на `prod`-стенде
добавьте эту команду в `cron` (`crontab -e`), например ежедневно в 03:00:

```
0 3 * * * pg_dump -U studgrade -h localhost studgrade > /var/backups/studgrade_$(date +\%F).sql
```

## Структура проекта

```
лр2/
  app/                 # исходный код приложения (модели, маршруты, шаблоны)
  deploy/studgrade.service   # systemd-юнит для прод-стенда (gunicorn)
  seed.py              # наполнение БД тестовыми данными
  wsgi.py              # точка входа
  requirements.txt
```

## Локальный запуск (для разработки)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py                  # создаёт БД и тестовые данные
python wsgi.py                  # http://127.0.0.1:5000
```

Тестовые учётные записи (создаются `seed.py`):

| Логин   | Пароль      | Роль                        |
|---------|-------------|-----------------------------|
| admin   | admin123    | сотрудник учебного отдела   |
| teacher | teacher123  | преподаватель                |

---

## Развёртывание для лабораторной работы №2 (виртуализация)

Ниже — план действий под пункты задания лр2 (гипервизор, ВМ, сеть,
доставка кода через git, запуск).

### 1. Гипервизор

VirtualBox или VMware Workstation — на выбор, оба подходят.

### 2. Образы ОС для стендов test / stage / prod

Берите **серверные** (headless) образы, не desktop:

- Ubuntu Server 22.04/24.04 LTS, либо
- Debian 12 (netinst)

Почему не desktop-версия: test/stage/prod — это стенды для веб-сервиса
без графического интерфейса, GUI (GNOME/KDE и т.п.) только расходует
RAM/CPU виртуалки и не нужен. Минимальный серверный образ ставится
быстрее, занимает меньше диска и ближе к тому, как реально
разворачивают такие сервисы в проде.

Создайте 3 ВМ: `test`, `stage`, `prod` (можно даже с одинаковыми
характеристиками — 1 vCPU / 1–2 GB RAM / 10–15 GB диска достаточно для
Flask-прототипа).

### 3. Объединение ВМ в одну сеть

Проще всего — сетевой адаптер каждой ВМ в режиме **"Внутренняя сеть"
(Internal Network)** или **"Сеть хоста" (Host-only)** с одним и тем же
именем сети на всех трёх машинах, плюс второй адаптер в режиме NAT —
чтобы у каждой ВМ был доступ в интернет для установки пакетов.

На каждой ВМ задайте статический IP в общей подсети, например:

```
test  — 192.168.56.10
stage — 192.168.56.11
prod  — 192.168.56.12
```

(в Ubuntu Server — через netplan, `/etc/netplan/*.yaml`, `netmask 255.255.255.0`).

Проверка (со скриншотом в отчёт) — с каждой машины пингуем две другие:

```bash
ping -c 3 192.168.56.11
ping -c 3 192.168.56.12
```

### 4. Установка средств разработки на стенде

На каждой ВМ:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### 5. Доставка кода из удалённого репозитория (git)

Залейте содержимое папки `лр2` в свой репозиторий (GitHub/GitLab), затем
на тестовом стенде:

```bash
git clone <URL-вашего-репозитория> studgrade
cd studgrade
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed.py
python wsgi.py            # прототип на скриптовом языке — запускаем как есть
```

Приложение поднимется на `http://<IP-стенда>:5000` — откройте в
браузере с хост-машины (адаптер NAT/host-only должен пробрасывать порт,
либо смотрите напрямую по IP ВМ, если сеть это позволяет) и сделайте
скриншот работающего интерфейса (страница логина/дашборд).

Для **stage** повторите тот же сценарий (git clone + venv + pip install
+ запуск) — это имитирует предпродакшн-проверку перед прод.

### 6. Прод-стенд (systemd + gunicorn)

На `prod` вместо dev-сервера Flask лучше показать более "боевой"
вариант через `gunicorn`, который уже есть в `requirements.txt`:

```bash
sudo mkdir -p /opt/studgrade
sudo cp -r ~/studgrade/* /opt/studgrade/
cd /opt/studgrade
python3 -m venv venv
venv/bin/pip install -r requirements.txt
venv/bin/python seed.py
sudo cp deploy/studgrade.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now studgrade
sudo systemctl status studgrade
```

`gunicorn` слушает только `127.0.0.1:8000` (не наружу) — снаружи
сервис отдаётся через nginx с TLS (см. следующий пункт), это же и
переживает перезагрузку/падение процесса (`Restart=on-failure`).

### 7. HTTPS (TLS) перед прод-стендом

П. 4.3.3 ТЗ требует, чтобы клиент и сервер общались по HTTPS (TLS не
ниже 1.2), поэтому на `prod` перед `gunicorn` должен стоять reverse-proxy
с TLS-терминацией:

```bash
sudo apt install -y nginx openssl
sudo mkdir -p /etc/ssl/studgrade
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/studgrade/studgrade.key \
  -out /etc/ssl/studgrade/studgrade.crt \
  -subj "/CN=studgrade.local"

sudo cp deploy/nginx-studgrade.conf /etc/nginx/sites-available/studgrade
sudo ln -s /etc/nginx/sites-available/studgrade /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Сертификат самоподписанный (для учебного стенда), браузер покажет
предупреждение о недоверенном сертификате — это ожидаемо, нужно принять
исключение и открыть `https://<IP-стенда>/`. Подробности — в
`deploy/nginx-studgrade.conf`.

### Что положить в отчёт (скриншоты)

1. Список ВМ в гипервизоре (test/stage/prod), их настройки сети.
2. `ip a` на каждой ВМ (видны IP-адреса).
3. `ping` от каждой ВМ к двум другим ("от всех ко всем").
4. `git clone` тестового стенда — вывод команды.
5. Установка venv/зависимостей (`pip install -r requirements.txt`).
6. Запущенное приложение — страница логина/дашборд в браузере (для
   test и stage — через `python wsgi.py`, для prod — через
   `systemctl status studgrade` и открытую страницу `https://<IP>/`).
7. Успешная настройка nginx (`nginx -t`, `systemctl status nginx`) и
   страница, открытая по `https://`.
