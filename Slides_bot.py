import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading

# إعداد سيرفر Flask ليبقى البوت نشطاً على Render
app = Flask(__name__)
@app.route('/')
def home():
    return "Slides Bot is Active!"

# ضع التوكن الخاص بك هنا
BOT_TOKEN = "8568933769:AAGPBh4YytR_K0HzVwUfDMhDSbX7Di57dtY"
bot = telebot.TeleBot(BOT_TOKEN)

# دالة استخراج النص من PDF
def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except:
        return None

# دالة التلخيص
def ai_summarize(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [{"role": "user", "content": f"لخص هذا النص:\n{text[:6000]}"}]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        return response.json()['choices'][0]['message']['content']
    except:
        return "⚠️ حدث خطأ أثناء التلخيص."

# معالجة الملفات (PDF)
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open("temp.pdf", 'wb') as f:
            f.write(downloaded_file)
        
        bot.reply_to(message, "📄 جاري معالجة الملف...")
        text = extract_text_from_pdf("temp.pdf")
        
        if text:
            summary = ai_summarize(text)
            bot.reply_to(message, summary)
        else:
            bot.reply_to(message, "❌ الملف غير قابل للقراءة.")
    except Exception as e:
        bot.reply_to(message, f"⚠️ خطأ: {str(e)}")

# معالجة النصوص
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'): return
    bot.reply_to(message, "✍️ جاري التلخيص...")
    bot.reply_to(message, ai_summarize(message.text))

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 البوت جاهز! أرسل لي نصاً أو ملف PDF.")

if __name__ == "__main__":
    # تشغيل Flask في الخلفية
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    
    # تصفير الاتصال وبدء البوت (حل جذري للتعارض)
    bot.remove_webhook()
    bot.infinity_polling()
