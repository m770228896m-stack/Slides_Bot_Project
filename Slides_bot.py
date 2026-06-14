import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading
import time

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Active!"

BOT_TOKEN = "8568933769:AAFCpNSXwVr8xy_5vk0-fkWr7WIYyPqzUzY"
OWNER_ID = 995412569
DB_FILE = "database.txt"
bot = telebot.TeleBot(BOT_TOKEN)

# --- دوال التحكم ---
def load_subscribers():
    subs = {OWNER_ID: "permanent"}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2: subs[int(parts[0])] = parts[1]
    return subs

def process_ai(text, translate=False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    prompt = f"لخص هذا النص العلمي بدقة:\n{text[:6000]}"
    if translate: prompt = f"ترجم النص للعربية ولخصه:\n{text[:6000]}"
    payload = {"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        return response.json()['choices'][0]['message']['content']
    except: return "⚠️ فشل الاتصال بالذكاء الاصطناعي."

# --- معالجة الأوامر ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == OWNER_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ إضافة مشترك", "📋 عرض المشتركين")
        bot.reply_to(message, "👑 أهلاً بك يا مالك البوت! اختر من القائمة:", reply_markup=markup)
    else:
        bot.reply_to(message, "👋 أهلاً بك! أرسل ملف PDF للبدء.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    # إزالة الأزرار القديمة والبدء بمعالجة جديدة
    msg = bot.reply_to(message, "⏳ جارٍ تحميل الملف...")
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.pdf", 'wb') as f: f.write(downloaded_file)
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ تلخيص", callback_data="sum"),
               telebot.types.InlineKeyboardButton("🌍 ترجمة وتلخيص", callback_data="trans"))
    bot.edit_message_text("📄 تم استلام الملف. اختر الإجراء:", message.chat.id, msg.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    translate = (call.data == "trans")
    bot.edit_message_text("⏳ جاري المعالجة (قد يستغرق وقتاً)...", call.message.chat.id, call.message.message_id)
    try:
        reader = PyPDF2.PdfReader("temp.pdf")
        text = "".join([p.extract_text() for p in reader.pages[:15] if p.extract_text()]) # قراءة أول 15 صفحة فقط للسرعة
        bot.send_message(call.message.chat.id, process_ai(text, translate), parse_mode="Markdown")
    except: bot.send_message(call.message.chat.id, "❌ خطأ في القراءة.")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.remove_webhook() # تصفية الاتصال
    bot.infinity_polling()
