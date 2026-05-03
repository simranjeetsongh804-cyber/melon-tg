import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import time

# ================= CONFIGURATION =================
# BotFather se mile tokens yahan dalein
BOT1_TOKEN = '8726393630:AAEvQvpppyIPBpSbRIDOhgH0kCg6TRiAnrI' 
BOT2_TOKEN = '8730248424:AAG57Xs8zws_Kc50UXEf4UuLONeEcNi5cAQ'

# Apne Private Channel ki ID yahan dalein (e.g., -100123456789)
DB_CHANNEL_ID = -6132381350 

# Apne Bots ke Usernames (Bina @ ke)
BOT1_USERNAME = 'melonhub_bot'
BOT2_USERNAME = 'melonvid_bot'
# =================================================

bot1 = telebot.TeleBot(BOT1_TOKEN)
bot2 = telebot.TeleBot(BOT2_TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running 24/7!"

# -------- BOT 1 LOGIC (Redirector) --------
@bot1.message_handler(commands=['start'])
def handle_bot1_start(message):
    text = message.text.split()
    if len(text) > 1:
        file_id = text[1] # Ye code (e.g. 10-20) uthayega
        markup = InlineKeyboardMarkup()
        btn = InlineKeyboardButton("📥 Download Now", url=f"https://t.me/{BOT2_USERNAME}?start={file_id}")
        markup.add(btn)
        bot1.send_message(message.chat.id, "✨ **Aapki file taiyar hai!**\n\nNiche diye gaye button par click karke Download karein.", reply_markup=markup, parse_mode='Markdown')

# -------- BOT 2 LOGIC (File Sender) --------
@bot2.message_handler(commands=['start'])
def handle_bot2_start(message):
    text = message.text.split()
    if len(text) > 1:
        data = text[1]
        bot2.send_message(message.chat.id, "⌛ **Files bheji ja rahi hain, kripya intezar karein...**", parse_mode='Markdown')
        
        # Check range (e.g. 10-20) or single ID (e.g. 10)
        if "-" in data:
            try:
                start_id, end_id = map(int, data.split("-"))
            except: return
        else:
            try:
                start_id = end_id = int(data)
            except: return

        for msg_id in range(start_id, end_id + 1):
            try:
                bot2.copy_message(chat_id=message.chat.id, from_chat_id=DB_CHANNEL_ID, message_id=msg_id)
                time.sleep(1) # Speed limit taaki bot ban na ho
            except Exception as e:
                print(f"Error copying message {msg_id}: {e}")
    else:
        # Normal messages ko ignore karega
        pass

# -------- RUNNING THE ENGINE --------
def run_flask():
    app.run(host="0.0.0.0", port=8000)

def start_polling():
    threading.Thread(target=lambda: bot1.infinity_polling()).start()
    bot2.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    start_polling()