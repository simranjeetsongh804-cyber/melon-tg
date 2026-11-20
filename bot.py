import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import time
import random
import os
import base64
import hmac
import hashlib

# ================= ULTRA SECURITY CONFIGURATION =================
BOT1_TOKEN = os.getenv('BOT1_TOKEN')
BOT2_TOKEN = os.getenv('BOT2_TOKEN')
LINK_SECRET = os.getenv('LINK_SECRET', 'melon_ultra_secret_key_change_me_2026').encode()

# Apni Telegram User IDs yahan dalein (sirf inko /genlink ka access milega)
ADMIN_IDS = [6132381350]

# Apne Private Channel ki ID yahan dalein
DB_CHANNEL_ID = -1003974946855

# Apne Naye Bots ke Usernames (Bina @ ke)
BOT1_USERNAME = 'melonclick_bot'
BOT2_USERNAME = 'melonshare_bot'
# ================================================================

if not BOT1_TOKEN or not BOT2_TOKEN:
    print("CRITICAL ERROR: Bot tokens are missing from Environment Variables!")

bot1 = telebot.TeleBot(BOT1_TOKEN)
bot2 = telebot.TeleBot(BOT2_TOKEN)
app = Flask(__name__)

user_cooldown = {}

# -------- SECURE TOKEN ENCODE / DECODE (NO RAW NUMBERS IN URL) --------
def encode_range_token(range_str: str) -> str:
    raw_bytes = range_str.strip().encode()
    sig = hmac.new(LINK_SECRET, raw_bytes, hashlib.sha256).digest()[:10]
    payload = raw_bytes + b"::" + sig
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")

def decode_range_token(token: str):
    try:
        padded = token + "=" * (-len(token) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode())
        if b"::" not in decoded:
            return None
        range_bytes, provided_sig = decoded.rsplit(b"::", 1)
        expected_sig = hmac.new(LINK_SECRET, range_bytes, hashlib.sha256).digest()[:10]
        if not hmac.compare_digest(provided_sig, expected_sig):
            return None

        range_str = range_bytes.decode()
        if "-" in range_str:
            parts = range_str.split("-")
            if len(parts) != 2:
                return None
            start_id, end_id = int(parts[0]), int(parts[1])
        else:
            start_id = end_id = int(range_str)

        if start_id <= 0 or end_id <= 0 or end_id < start_id:
            return None
        return start_id, end_id
    except Exception:
        return None

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@app.route('/')
def home():
    return "Secure Bot is Running 24/7!"

# -------- ADMIN LINK GENERATOR COMMAND (/genlink 602-706) --------
def handle_genlink_command(bot_instance, message):
    if not is_admin(message.from_user.id):
        return

    parts = message.text.strip().split()
    if len(parts) != 2:
        bot_instance.reply_to(
            message,
            "⚠️ **Usage:** `/genlink 602-706` (or single ID like `/genlink 602`)",
            parse_mode='Markdown'
        )
        return

    range_input = parts[1].strip()
    token = encode_range_token(range_input)
    parsed = decode_range_token(token)
    if not parsed:
        bot_instance.reply_to(
            message,
            "❌ **Invalid range!** Example: `/genlink 602-706`",
            parse_mode='Markdown'
        )
        return

    start_id, end_id = parsed
    link = f"https://t.me/{BOT1_USERNAME}?start={token}"
    reply_text = (
        f"✅ **Secure Link Generated!**\n"
        f"📦 **Range:** `{start_id}` to `{end_id}` (`{end_id - start_id + 1}` items)\n\n"
        f"🔗 **Copy & Paste Link:**\n`{link}`"
    )
    bot_instance.reply_to(message, reply_text, parse_mode='Markdown', disable_web_page_preview=True)

@bot1.message_handler(commands=['genlink'])
def bot1_genlink(message):
    handle_genlink_command(bot1, message)

@bot2.message_handler(commands=['genlink'])
def bot2_genlink(message):
    handle_genlink_command(bot2, message)

# -------- BOT 1 LOGIC (Redirector & Welcome with Link) --------
DOWNLOAD_BUTTON_PHOTO_ID = 361
WELCOME_PHOTOS = [345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359]

@bot1.message_handler(commands=['start'])
def handle_bot1_start(message):
    text = message.text.split()
    user_id = message.from_user.id
    chat_id = message.chat.id

    current_time = time.time()
    if user_id in user_cooldown and current_time - user_cooldown[user_id] < 2:
        return
    user_cooldown[user_id] = current_time

    if len(text) > 1:
        token = text[1]
        parsed = decode_range_token(token)
        if not parsed:
            bot1.send_message(chat_id, "❌ **Invalid or expired link!**", parse_mode='Markdown')
            return

        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("📥 Download Now", url=f"https://t.me/{BOT2_USERNAME}?start={token}")
        markup.add(btn)

        caption_text = "📥 **Click below to download your file:**\n\n⏳ *Note: This download button will automatically delete in 5 minutes!*"

        try:
            sent_msg = bot1.copy_message(
                chat_id=chat_id,
                from_chat_id=DB_CHANNEL_ID,
                message_id=DOWNLOAD_BUTTON_PHOTO_ID,
                caption=caption_text,
                reply_markup=markup,
                parse_mode='Markdown'
            )
        except Exception:
            sent_msg = bot1.send_message(chat_id, caption_text, reply_markup=markup, parse_mode='Markdown')

        def delete_button_msg():
            time.sleep(300)
            try:
                bot1.delete_message(chat_id, sent_msg.message_id)
            except Exception:
                pass

        threading.Thread(target=delete_button_msg, daemon=True).start()

    else:
        random_photo_id = random.choice(WELCOME_PHOTOS)
        welcome_msg = (
            f"<b>Hi</b> <a href='tg://user?id={user_id}'>User</a>\n"
            f"<b>Welcome to</b> <a href='https://t.me/melonxhub'>@melonxhub</a>\n\n"
            f"Click the link above to join our main hub!"
        )

        try:
            bot1.copy_message(
                chat_id=chat_id,
                from_chat_id=DB_CHANNEL_ID,
                message_id=random_photo_id,
                caption=welcome_msg,
                parse_mode='HTML'
            )
        except Exception:
            try:
                bot1.send_message(chat_id, welcome_msg, parse_mode='HTML')
            except Exception:
                pass

# -------- BOT 2 LOGIC (Fast Unlimited Secure File Sender) --------
@bot2.message_handler(commands=['start'])
def handle_bot2_start(message):
    text = message.text.split()

    if len(text) > 1:
        token = text[1]
        parsed = decode_range_token(token)
        if not parsed:
            bot2.send_message(message.chat.id, "❌ **Invalid or tampered link!**", parse_mode='Markdown')
            return

        start_id, end_id = parsed
        total_files = end_id - start_id + 1
        bot2.send_message(
            message.chat.id,
            f"⚡ **Sending {total_files} files quickly...**",
            parse_mode='Markdown'
        )

        for msg_id in range(start_id, end_id + 1):
            try:
                bot2.copy_message(
                    chat_id=message.chat.id,
                    from_chat_id=DB_CHANNEL_ID,
                    message_id=msg_id
                )
                time.sleep(0.3)
            except Exception as e:
                print(f"Error copying message {msg_id}: {e}")
    else:
        bot2.send_message(
            message.chat.id,
            "⚠️ **Please use the official link from @melonxhub to get files.**",
            parse_mode='Markdown'
        )

# -------- RUNNING THE ENGINE --------
def run_flask():
    app.run(host="0.0.0.0", port=8000)

def start_polling():
    threading.Thread(target=lambda: bot1.infinity_polling(skip_pending=True), daemon=True).start()
    bot2.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    start_polling()
