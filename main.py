import logging
import requests
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "PUT_YOUR_BOT_TOKEN_HERE"
OWNER_ID = 123456789  # Replace with your Telegram user ID
AUTHORIZED_FILE = "authorized_users.json"

def load_authorized_users():
    try:
        with open(AUTHORIZED_FILE, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_authorized_users(users):
    with open(AUTHORIZED_FILE, "w") as f:
        json.dump(list(users), f)

authorized_users = load_authorized_users()

def is_authorized(user_id):
    return user_id == OWNER_ID or str(user_id) in authorized_users

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized access.")
        return
    await update.message.reply_text(
        "👋 Welcome! Send Instagram credentials in this format:\n\n`username:password`",
        parse_mode="Markdown"
    )

async def authorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You're not allowed to authorize users.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Use: /authorize user_id")
        return
    user_id = context.args[0]
    authorized_users.add(user_id)
    save_authorized_users(authorized_users)
    await update.message.reply_text(f"✅ User {user_id} is now authorized.")

async def unauthorize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ You're not allowed to unauthorize users.")
        return
    if not context.args:
        await update.message.reply_text("⚠️ Use: /unauthorize user_id")
        return
    user_id = context.args[0]
    if user_id in authorized_users:
        authorized_users.remove(user_id)
        save_authorized_users(authorized_users)
        await update.message.reply_text(f"🗑️ User {user_id} has been removed.")
    else:
        await update.message.reply_text("⚠️ User not found.")

async def handle_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("❌ Unauthorized access.")
        return
    text = update.message.text.strip()
    if ":" not in text:
        await update.message.reply_text("⚠️ Invalid format. Use: username:password")
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
    app.add_handler(CommandHandler("authorize", authorize))
    app.add_handler(CommandHandler("unauthorize", unauthorize))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credentials))
    app.run_polling()