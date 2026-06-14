import os
import telebot
import requests
from telebot import types
from flask import Flask
from datetime import datetime, timedelta
import PyPDF2

# سيرفر ويب للحفاظ على البوت نشطاً
app = Flask(__name__)
@app.route('/')
def home():
    return "سلايدز بوت يعمل الآن مع دعم الـ PDF!"

BOT_TOKEN = "8568933769:AAGPBh4YytR_K0HzVwUfDMhDSbX7Di57dtY"
OWNER_ID = 995412569
DB_FILE = "database.txt"

# تحميل المشتركين
def load_subscribers():
    subs = {OWNER_ID: "permanent"}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    subs[int(parts[0])] = parts[1]
    return subs

SUBSCRIBERS = load_subscribers()
bot = telebot.TeleBot(BOT_TOKEN)

# دالة استخراج النص من PDF
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    return text

# دالة التلخيص الذكي
def ai_summarize(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [{"role": "user", "content": f"لخص هذا النص العلمي/الطبي للعربية مع الحفاظ على المصطلحات بالإنجليزية:\n{text[:6000]}"}]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except:
        return "⚠️ حدث خطأ أثناء المعالجة."
    return "📚 عذراً، السيرفر مشغول."

# معالجة الملفات (PDF)
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open("temp.pdf", 'wb') as new_file:
        new_file.write(downloaded_file)
    
    bot.reply_to(message, "📄 جاري قراءة الملف وتلخيصه...")
    text = extract_text_from_pdf("temp.pdf")
    summary = ai_summarize(text)
    bot.reply_to(message, summary, parse_mode="Markdown")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "أهلاً بك! أرسل لي نصاً أو ملف PDF وسأقوم بتلخيصه فوراً.")

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.infinity_polling()
