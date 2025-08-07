import logging
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"  # حط توكن بوتك هنا
OWNER_ID = 123456789  # ممكن تخليه موجود بس مش راح يستخدم

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send Instagram credentials in this format:\n\nusername:password"
    )

async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if ":" not in text:
        await update.message.reply_text("⚠️ Invalid format. Use:\nusername:password")
        return

    username, password = text.split(":", 1)
    session_id = await extract_session_id(username, password)
    if session_id:
        await update.message.reply_text(f"✅ Session ID:\n`{session_id}`", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Failed to extract Session ID. Check credentials.")

async def extract_session_id(username, password):
    with requests.Session() as session:
        try:
            session.headers.update({
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.instagram.com/accounts/login/"
            })
            r = session.get("https://www.instagram.com/accounts/login/")
            csrf = session.cookies.get("csrftoken", "")

            payload = {
                'username': username,
                'enc_password': f"#PWD_INSTAGRAM_BROWSER:0:&:{password}",
                'queryParams': {},
                'optIntoOneTap': 'false'
            }
            headers = {
                "X-CSRFToken": csrf,
                "X-Requested-With": "XMLHttpRequest"
            }
            login = session.post("https://www.instagram.com/accounts/login/ajax/", data=payload, headers=headers)
            if login.status_code == 200 and login.json().get("authenticated"):
                return session.cookies.get("sessionid")
        except Exception as e:
            print("Error:", e)
    return None

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
    app.run_polling()
