import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading

app = Flask(__name__)
@app.route('/')
def home(): return "Bot is Active!"

BOT_TOKEN = "8568933769:AAHtR77_EnDGXPSEW1HMPf4jHHKo0mOXIZs"
bot = telebot.TeleBot(BOT_TOKEN)

# 1. دالة استخراج النص (تقرأ كل شيء مهما كان الحجم)
def extract_all_text(file_path):
    try:
        text = ""
        reader = PyPDF2.PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except: return None

# 2. دالة التلخيص والترجمة
def process_text(text, translate=False):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    
    prompt = f"لخص هذا النص العلمي بدقة:\n{text[:8000]}"
    if translate:
        prompt = f"قم بترجمة هذا النص إلى العربية وتلخيصه بشكل مبسط:\n{text[:8000]}"
        
    payload = {"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": prompt}]}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        return response.json()['choices'][0]['message']['content']
    except: return "⚠️ حدث خطأ أثناء المعالجة."

# 3. معالجة الملف
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.pdf", 'wb') as f: f.write(downloaded_file)
    
    # إضافة أزرار خيار الترجمة
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("✅ تلخيص فقط", callback_data="sum"),
               telebot.types.InlineKeyboardButton("🌍 تلخيص وترجمة", callback_data="trans"))
    
    bot.reply_to(message, "📄 تم استلام الملف. كيف تريدني أن أعمل عليه؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    translate = (call.data == "trans")
    bot.edit_message_text("⏳ جاري العمل... قد يستغرق هذا وقتاً للملفات الكبيرة.", call.message.chat.id, call.message.message_id)
    
    text = extract_all_text("temp.pdf")
    if text:
        result = process_text(text, translate)
        bot.send_message(call.message.chat.id, result, parse_mode="Markdown")
    else:
        bot.send_message(call.message.chat.id, "❌ خطأ في قراءة الـ PDF.")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.remove_webhook()
    bot.infinity_polling()
