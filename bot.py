import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import time
import random
import os

# ================= ULTRA SECURITY CONFIGURATION =================
BOT1_TOKEN = os.getenv('BOT1_TOKEN')
BOT2_TOKEN = os.getenv('BOT2_TOKEN')

# Apne Private Channel ki ID yahan dalein
DB_CHANNEL_ID = -1003974946855 

# Apne Naye Bots ke Usernames (Bina @ ke)
BOT1_USERNAME = 'Melonclick_bot'
BOT2_USERNAME = 'Melonshare_bot'
# ================================================================

# Safety check agar tokens na milein
if not BOT1_TOKEN or not BOT2_TOKEN:
    print("CRITICAL ERROR: Bot tokens are missing from Environment Variables!")

bot1 = telebot.TeleBot(BOT1_TOKEN)
bot2 = telebot.TeleBot(BOT2_TOKEN)
app = Flask(__name__)

# Anti-Spam dictionary to track user requests
user_cooldown = {}

@app.route('/')
def home():
    return "Secure Bot is Running 24/7!"

# -------- BOT 1 LOGIC (Redirector & Welcome with Link) --------
DOWNLOAD_BUTTON_PHOTO_ID = 361 
WELCOME_PHOTOS = [345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359]

@bot1.message_handler(commands=['start'])
def handle_bot1_start(message):
    text = message.text.split()
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # Anti-flood check for Bot 1
    current_time = time.time()
    if user_id in user_cooldown and current_time - user_cooldown[user_id] < 2:
        return
    user_cooldown[user_id] = current_time

    if len(text) > 1:
        file_id = text[1] 
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("📥 Download Now", url=f"https://t.me/{BOT2_USERNAME}?start={file_id}")
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
        except Exception as e:
            sent_msg = bot1.send_message(chat_id, caption_text, reply_markup=markup, parse_mode='Markdown')
        
        # Background thread to auto-delete the download button message after 5 minutes (300 seconds)
        def delete_button_msg():
            time.sleep(300)
            try:
                bot1.delete_message(chat_id, sent_msg.message_id)
            except:
                pass
        
        threading.Thread(target=delete_button_msg).start()
        
    else:
        random_photo_id = random.choice(WELCOME_PHOTOS)
        welcome_msg = f"<b>Hi</b> <a href='tg://user?id={user_id}'>User</a>\n<b>Welcome to</b> <a href='https://t.me/melonxhub'>@melonxhub</a>\n\nClick the link above to join our main hub!"
        
        try:
            bot1.copy_message(
                chat_id=chat_id, 
                from_chat_id=DB_CHANNEL_ID, 
                message_id=random_photo_id, 
                caption=welcome_msg,
                parse_mode='HTML'
            )
        except Exception as e:
            try:
                bot1.send_message(chat_id, welcome_msg, parse_mode='HTML')
            except:
                pass

# -------- BOT 2 LOGIC (Fast Secure File Sender) --------
@bot2.message_handler(commands=['start'])
def handle_bot2_start(message):
    text = message.text.split()
    user_id = message.from_user.id
    
    if len(text) > 1:
        data = text[1]
        
        if not all(c.isdigit() or c == '-' for c in data):
            bot2.send_message(message.chat.id, "❌ **Invalid Request!**", parse_mode='Markdown')
            return

        bot2.send_message(message.chat.id, "⚡ **Sending your files quickly...**", parse_mode='Markdown')
        
        if "-" in data:
            try:
                parts = data.split("-")
                if len(parts) == 2:
                    start_id, end_id = int(parts[0]), int(parts[1])
                    if end_id - start_id > 50:
                        end_id = start_id + 50
                else:
                    return
            except: 
                return
        else:
            try:
                start_id = end_id = int(data)
            except: 
                return

        for msg_id in range(start_id, end_id + 1):
            try:
                bot2.copy_message(chat_id=message.chat.id, from_chat_id=DB_CHANNEL_ID, message_id=msg_id)
                time.sleep(0.3) # Fast delay to send files quickly without hitting Telegram FloodWait
            except Exception as e:
                print(f"Error copying message {msg_id}: {e}")
    else:
        bot2.send_message(message.chat.id, "⚠️ **Please use the official link from @melonxhub to get files.**", parse_mode='Markdown')

# -------- RUNNING THE ENGINE --------
def run_flask():
    app.run(host="0.0.0.0", port=8000)

def start_polling():
    threading.Thread(target=lambda: bot1.infinity_polling(skip_pending=True)).start()
    bot2.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    start_polling()
