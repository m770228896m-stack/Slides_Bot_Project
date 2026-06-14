import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading
import time

# --- الإعدادات ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Slides Bot is Active!"

BOT_TOKEN = "8568933769:AAHtR77_EnDGXPSEW1HMPf4jHHKo0mOXIZs"
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
                if len(parts) == 2:
                    subs[int(parts[0])] = parts[1]
    return subs

# --- دالة استخراج النص (مُحسنة) ---
def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # نقرأ أول 10 صفحات فقط لتجنب الضغط الكبير على الذاكرة
            for page in reader.pages[:10]:
                content = page.extract_text()
                if content: text += content + "\n"
        return text
    except: return None

# --- دالة التلخيص (مُحسنة بزيادة وقت الانتظار) ---
def ai_summarize(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [{"role": "user", "content": f"لخص هذا النص العلمي للعربية:\n{text[:4000]}"}]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=90) # زيادة وقت الانتظار
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return f"⚠️ خطأ في الاستجابة: {response.status_code}"
    except: return "⚠️ فشل الاتصال بالذكاء الاصطناعي. حاول مرة أخرى."

# --- معالجة الرسائل ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🔥 أهلاً بك في سلايدز بوت! أرسل لي نصاً أو ملف PDF للتلخيص.")

@bot.message_handler(content_types=['document', 'text'])
def handle_all(message):
    user_id = message.from_user.id
    subs = load_subscribers()
    
    if user_id not in subs:
        bot.reply_to(message, "❌ عذراً، لست مشتركاً.")
        return

    if message.content_type == 'document':
        msg = bot.reply_to(message, "📄 جاري معالجة الملف...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.pdf", 'wb') as f: f.write(downloaded_file)
        
        text = extract_text_from_pdf("temp.pdf")
        if text: 
            summary = ai_summarize(text)
            bot.edit_message_text(summary, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        else: bot.edit_message_text("❌ تعذر قراءة الملف.", chat_id=message.chat.id, message_id=msg.message_id)
    
    elif message.content_type == 'text':
        if message.text.startswith('/'): return
        msg = bot.reply_to(message, "✍️ جاري التلخيص...")
        summary = ai_summarize(message.text)
        bot.edit_message_text(summary, chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    bot.remove_webhook()
    bot.infinity_polling()
