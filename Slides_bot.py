import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading

# --- الإعدادات ---
app = Flask(__name__)
@app.route('/')
def home(): return "Slides Bot is Active!"

# تم وضع التوكن الجديد هنا
BOT_TOKEN = "8568933769:AAFCpNSXwVr8xy_5vk0-fkWr7WIYyPqzUzY"
OWNER_ID = 995412569
DB_FILE = "database.txt"
bot = telebot.TeleBot(BOT_TOKEN)

# --- دوال قاعدة البيانات ---
def load_subscribers():
    subs = {OWNER_ID: "permanent"}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2: subs[int(parts[0])] = parts[1]
    return subs

# --- معالجة النصوص والملفات ---
def process_ai(text, translate=False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    prompt = f"لخص هذا النص العلمي بدقة:\n{text[:8000]}"
    if translate: prompt = f"ترجم هذا النص للعربية ولخصه:\n{text[:8000]}"
    payload = {"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        return response.json()['choices'][0]['message']['content']
    except: return "⚠️ حدث خطأ في الاتصال بالذكاء الاصطناعي."

@bot.message_handler(commands=['start'])
def start(message): bot.reply_to(message, "🔥 أهلاً بك في سلايدز بوت! أرسل لي ملف PDF للبدء.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.from_user.id not in load_subscribers():
        bot.reply_to(message, "❌ لست مشتركاً.")
        return
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.pdf", 'wb') as f: f.write(downloaded_file)
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ تلخيص", callback_data="sum"),
               telebot.types.InlineKeyboardButton("🌍 ترجمة وتلخيص", callback_data="trans"))
    bot.reply_to(message, "📄 تم استلام الملف. اختر الإجراء:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    translate = (call.data == "trans")
    bot.edit_message_text("⏳ جاري المعالجة...", call.message.chat.id, call.message.message_id)
    try:
        reader = PyPDF2.PdfReader("temp.pdf")
        text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        bot.send_message(call.message.chat.id, process_ai(text, translate), parse_mode="Markdown")
    except: bot.send_message(call.message.chat.id, "❌ خطأ في قراءة الملف.")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.remove_webhook() # إزالة أي اتصال معلق
    bot.infinity_polling()
