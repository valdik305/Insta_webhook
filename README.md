# 🤖 Instagram Auto-Reply Bot (FastAPI)

Этот проект представляет собой локальный сервер на Python (FastAPI), который автоматически отслеживает новые комментарии под постами в Instagram и отправляет пользователям личные сообщения (Direct) с заданной ссылкой, а также оставляет публичный ответ под комментарием.

Бот работает через официальный **Instagram Graph API** и **Webhooks**, не используя сторонние платные сервисы.

## 🛠️ Стек технологий
*   **Python 3.10+**
*   **FastAPI** — веб-фреймворк для приема вебхуков.
*   **Uvicorn** — ASGI-сервер.
*   **HTTPX** — асинхронный HTTP-клиент для запросов к API Meta.
*   **python-dotenv** — для безопасного хранения токенов.
*   **Ngrok** (для локальной разработки) — для проброса локального сервера в интернет.

---

## 🚀 Пошаговая инструкция по развертыванию

### Шаг 1: Подготовка окружения
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/ваш-ник/Insta_webhook.git
   cd Insta_webhook
   
Создайте виртуальное окружение и активируйте его:

bash
python3 -m venv venv
source venv/bin/activate  # Для Mac/Linux
# venv\Scripts\activate   # Для Windows
Установите зависимости:

bash
pip install -r requirements.txt
Шаг 2: Настройка секретов (.env)

Создайте файл .env в корне проекта (на основе .env.example) и заполните его:

env
# Пароль для верификации вебхука (придумайте любой)
VERIFY_TOKEN=my_super_secret_token

# Основной секрет приложения (App Settings -> Basic)
APP_SECRET=ваш_app_secret

# ВАЖНО: Для Instagram Login используется вложенный секрет!
# (Вкладка "Сценарии использования" -> "Настройка API для входа в Instagram")
INSTAGRAM_APP_SECRET=ваш_instagram_app_secret

# Токен доступа (Instagram User Access Token, начинается на IG...)
ACCESS_TOKEN=ваш_instagram_access_token

# ID вашего Instagram Business аккаунта 
IG_USER_ID=ваш id

Шаг 3: Настройка Meta for Developers

Создайте приложение на developers.facebook.com.
Добавьте продукт Instagram API with Instagram Login (или Facebook Login, в зависимости от вашего сценария).
В настройках Webhooks укажите:

Callback URL: https://<ваш-домен-ngrok>.ngrok-free.app/webhook
Verify Token: Тот же, что в .env (VERIFY_TOKEN).
Подпишитесь на события: comments и messages.
Шаг 4: Запуск и тестирование

Запустите Ngrok (в отдельном терминале):

bash
ngrok http 8001
Скопируйте HTTPS-ссылку и обновите Callback URL в панели Meta.
Запустите сервер:

bash
uvicorn main:app --reload --port 8001
Напишите комментарий со словом «бот» под любым постом. Бот должен отправить ЛС и публичный ответ.
⚠️ Известные тонкости и проблемы (Troubleshooting)

При разработке мы столкнулись с рядом неочевидных проблем Meta API. Вот их решения:

Ошибка 403 Forbidden на POST /webhook:

Причина: Meta подписывает вебхуки Instagram не основным APP_SECRET, а вложенным INSTAGRAM_APP_SECRET.
Решение: В коде добавлена проверка обоих секретов. Убедитесь, что INSTAGRAM_APP_SECRET указан в .env.
Ошибка 2534039 (App is not connected to the business):

Причина: Meta не видит связи между приложением и бизнес-аккаунтом для отправки сообщений.
Решение: В Meta Business Suite (business.facebook.com) зайдите в Настройки → Маршрутизация переписок (Conversation Routing) и назначьте ваше приложение как «Приложение по умолчанию» (Default Routing App) для вашего Instagram-аккаунта.
Ошибка Cannot parse access token:

Причина: Несовместимость токена и домена API. Facebook-токены (EAA...) не работают с graph.instagram.com, а Instagram-токены (IG...) не работают с graph.facebook.com.
Решение: Если вы используете Instagram Login, все запросы (и ЛС, и публичные ответы) должны идти через https://graph.instagram.com/.... Если Facebook Login — через https://graph.facebook.com/....
Вебхуки не приходят (Тишина в терминале):

Убедитесь, что приложение переключено в режим Live (Опубликовано).
Убедитесь, что аккаунт, с которого вы пишете комментарий, является Администратором приложения или добавлен в Тестировщики Instagram и принял приглашение.
Ngrok меняет ссылку:

Бесплатная версия Ngrok выдает новую ссылку при каждом перезапуске. Придется обновлять её в панели Meta. Для стабильной работы рекомендуется купить постоянный домен (например, на Cloudflare) или использовать платную версию Ngrok с зарезервированным доменом.
📄 Лицензия

MIT