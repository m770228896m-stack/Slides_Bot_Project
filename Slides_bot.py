import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading
import time

# --- الإعدادات الأساسية ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Slides Bot is Active!"

BOT_TOKEN = "8568933769:AAGPBh4YytR_K0HzVwUfDMhDSbX7Di57dtY"
OWNER_ID = 995412569
DB_FILE = "database.txt"
bot = telebot.TeleBot(BOT_TOKEN)

# --- دوال قاعدة البيانات (نظام المالك) ---
def load_subscribers():
    subs = {OWNER_ID: "permanent"}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) == 2:
                    subs[int(parts[0])] = parts[1]
    return subs

# --- دالة استخراج النص من PDF ---
def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content: text += content + "\n"
        return text
    except: return None

# --- دالة التلخيص ---
def ai_summarize(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [{"role": "user", "content": f"لخص هذا النص العلمي للعربية:\n{text[:6000]}"}]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        return response.json()['choices'][0]['message']['content']
    except: return "⚠️ فشل في الاتصال بالذكاء الاصطناعي."

# --- معالجة الرسائل ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 أهلاً بك في سلايدز بوت! أرسل لي نصاً أو ملف PDF للتلخيص.")

@bot.message_handler(content_types=['document', 'text'])
def handle_all(message):
    user_id = message.from_user.id
    subs = load_subscribers()
    
    # فحص الاشتراك
    if user_id not in subs:
        bot.reply_to(message, "❌ عذراً، لست مشتركاً في البوت.")
        return

    # معالجة ملف PDF
    if message.content_type == 'document':
        bot.reply_to(message, "📄 جاري قراءة الملف...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.pdf", 'wb') as f: f.write(downloaded_file)
        
        text = extract_text_from_pdf("temp.pdf")
        if text: bot.reply_to(message, ai_summarize(text), parse_mode="Markdown")
        else: bot.reply_to(message, "❌ تعذر قراءة الملف.")
    
    # معالجة النص
    elif message.content_type == 'text':
        if message.text.startswith('/'): return
        bot.reply_to(message, "✍️ جاري التلخيص...")
        bot.reply_to(message, ai_summarize(message.text), parse_mode="Markdown")

# --- بدء التشغيل ---
if __name__ == "__main__":
    time.sleep(2) # تأخير بسيط لبدء السيرفر
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.remove_webhook()
    bot.infinity_polling()
