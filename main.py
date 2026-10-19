import os
import re
import hmac
import hashlib
import httpx
from fastapi import FastAPI, Request, Response, HTTPException, BackgroundTasks
from dotenv import load_dotenv


load_dotenv()
app = FastAPI()

# ==========================================
# 1. НАСТРОЙКИ (ЗАМЕНИТЕ НА СВОИ ДАННЫЕ)
# ==========================================
APP_SECRET = os.getenv("APP_SECRET")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
IG_USER_ID = os.getenv("IG_USER_ID")

# ==========================================
# 2. БЕЗОПАСНОСТЬ
# ==========================================
def verify_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return False

    # Список секретов для проверки (основной + Instagram)
    secrets_to_try = [APP_SECRET]

    # Добавляем Instagram секрет, если он задан в .env
    ig_secret = os.getenv("INSTAGRAM_APP_SECRET")
    if ig_secret:
        secrets_to_try.append(ig_secret)

    for secret in secrets_to_try:
        expected_sig = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(f"sha256={expected_sig}", signature):
            print(f"✅ Подпись совпала с секретом: {secret[:5]}...")
            return True

    print("❌ Ни один из секретов не подошел.")
    return False


# ==========================================
# 3. ВЕРИФИКАЦИЯ ВЕБХУКА (GET)
# ==========================================
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return Response(content=params.get("hub.challenge"), media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification failed")


# ==========================================
# 4. ПРИЕМ СОБЫТИЙ (POST)
# ==========================================
@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    signature = request.headers.get("X-Hub-Signature-256")
    body = await request.body()

    if not verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()

    if data.get("object") == "instagram":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                if change.get("field") == "comments":
                    val = change.get("value", {})
                    comment_id = val.get("id")
                    text = val.get("text", "")
                    from_id = val.get("from", {}).get("id")

                    # Защита эхо (игнорируем свои же ответы)
                    if from_id == IG_USER_ID:
                        continue

                    print(f"📩 Новый комментарий: '{text}' (ID: {comment_id})")
                    background_tasks.add_task(process_comment, comment_id, text)

    return {"status": "ok"}


# ==========================================
# 5. ЛОГИКА ОБРАБОТКИ
# ==========================================
async def process_comment(comment_id: str, text: str):
    text_lower = text.lower()

    KEYWORD_LINKS = {
        "бот": "https://your-site.com/visa-info",
        "хочу": "https://github.com/valdik305/Insta_webhook,\n Если лень заморачиваться я могу помочь с подключением !",
        "локация": "https://maps.app.goo.gl/2ksGkXXQQZvA1bW99?g_st=ic",
        "инфо": "https://your-site.com/about-us"
    }

    matched_keyword = None
    link_to_send = None

    for keyword, link in KEYWORD_LINKS.items():
        # Регулярное выражение \b ищет точное совпадение слова (с учетом знаков препинания)
        if re.search(rf'\b{keyword}\b', text_lower):
            matched_keyword = keyword
            link_to_send = link
            break

    if matched_keyword:
        print(f"🤖 Найдено слово '{matched_keyword}'. Отправляем в ЛС...")

        # 1. Отправляем сообщение в Direct с нужной ссылкой
        dm_success = await send_private_reply(
            comment_id,
            f"Привет! Вот ссылка, которую вы просили: {link_to_send}"
        )

        # 2. Если сообщение в ЛС ушло успешно, оставляем публичный комментарий
        if dm_success:
            print(f"💬 Оставляем публичный ответ под комментарием...")
            await send_public_reply(comment_id, "Ссылка отправлена вам в личные сообщения! 📩")
        else:
            await send_public_reply(comment_id,
                                    "Не удалось отправить сообщение. Пожалуйста, откройте доступ к личным сообщениям (Direct) и напишите нам!")


async def send_private_reply(comment_id: str, message_text: str) -> bool:
    """Отправляет сообщение в Direct. Возвращает True, если успешно."""
    url = f"https://graph.instagram.com/v19.0/{IG_USER_ID}/messages"
    #url = f"https://graph.facebook.com/v19.0/{IG_USER_ID}/messages"
    payload = {
        "recipient": {"comment_id": comment_id},
        "message": {"text": message_text}
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ Успешно отправлено в ЛС!")
            return True
        except httpx.HTTPStatusError as e:
            print(f"❌ Ошибка отправки в ЛС: {e.response.text}")
            return False
        except Exception as e:
            print(f"❌ Ошибка сети (ЛС): {e}")
            return False


async def send_public_reply(comment_id: str, message_text: str):
    """Отправляет публичный ответ под комментарием (Instagram Login)"""
    # Для Instagram-токена используем graph.instagram.com
    url = f"https://graph.instagram.com/v19.0/{comment_id}/replies"
    payload = {"message": message_text}
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print(f"✅ Публичный ответ оставлен!")
        except httpx.HTTPStatusError as e:
            print(f"❌ Ошибка публичного ответа: {e.response.text}")
        except Exception as e:
            print(f"❌ Ошибка сети (публичный): {e}")
