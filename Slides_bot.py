import os
import telebot
import requests
from flask import Flask
import PyPDF2
import threading

# إعداد السيرفر للحفاظ على البوت نشطاً
app = Flask(__name__)
@app.route('/')
def home():
    return "Slides Summarizer Bot is Live!"

BOT_TOKEN = "8568933769:AAGPBh4YytR_K0HzVwUfDMhDSbX7Di57dtY"
bot = telebot.TeleBot(BOT_TOKEN)

# دالة استخراج النص من ملف PDF
def extract_text_from_pdf(file_path):
    try:
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
        return text
    except:
        return None

# دالة إرسال النص للذكاء الاصطناعي للتلخيص
def ai_summarize(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemma-2-9b-it:free",
        "messages": [{"role": "user", "content": f"لخص هذا النص العلمي:\n{text[:6000]}"}]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except:
        return "⚠️ حدث خطأ أثناء التلخيص."

# معالجة أي ملف PDF يتم إرساله
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    with open("doc.pdf", 'wb') as f:
        f.write(downloaded_file)
    
    bot.reply_to(message, "📄 جاري قراءة الملف وتلخيصه...")
    text = extract_text_from_pdf("doc.pdf")
    
    if text:
        summary = ai_summarize(text)
        bot.reply_to(message, summary, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ لم أتمكن من قراءة هذا الملف.")

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "👋 أهلاً! أرسل لي أي ملف PDF وسأقوم بتلخيصه لك فوراً.")

if __name__ == "__main__":
    # تشغيل السيرفر في الخلفية
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    # تصفير الاتصال وبدء البوت
    bot.remove_webhook()
    bot.infinity_polling()
