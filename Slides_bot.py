import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading

# إعداد السيرفر
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Active!"

BOT_TOKEN = "8568933769:AAFCpNSXwVr8xy_5vk0-fkWr7WIYyPqzUzY"
OWNER_ID = 995412569
DB_FILE = "database.txt"
bot = telebot.TeleBot(BOT_TOKEN)

# دالة التلخيص المتينة
def process_ai(text, translate=False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    prompt = f"لخص هذا النص العلمي:\n{text[:5000]}"
    if translate: prompt = f"قم بترجمة هذا النص إلى العربية وتلخيصه:\n{text[:5000]}"
    
    payload = {"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        data = response.json()
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        else:
            return f"⚠️ خطأ في الاستجابة: {data}"
    except Exception as e: return f"⚠️ خطأ: {str(e)}"

# أوامر المالك العامة
@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == OWNER_ID:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("➕ إضافة مشترك", "📋 عرض المشتركين")
        bot.reply_to(message, "👑 أهلاً بك يا مالك البوت! القائمة مفعلة.", reply_markup=markup)
    else:
        bot.reply_to(message, "👋 أهلاً! أرسل ملف PDF للتلخيص.")

# معالجة الملفات (تظهر أزرار التلخيص والترجمة هنا)
@bot.message_handler(content_types=['document'])
def handle_docs(message):
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
    bot.edit_message_text("⏳ جاري المعالجة (الرجاء الانتظار)...", call.message.chat.id, call.message.message_id)
    try:
        reader = PyPDF2.PdfReader("temp.pdf")
        text = "".join([p.extract_text() for p in reader.pages[:10] if p.extract_text()])
        result = process_ai(text, translate)
        bot.edit_message_text(result, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ خطأ: {str(e)}", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.remove_webhook()
    bot.infinity_polling()
