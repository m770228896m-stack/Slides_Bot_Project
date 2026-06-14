import os
import telebot
import requests
from telebot import types
from flask import Flask
from datetime import datetime, timedelta

# 🌐 سيرفر وهمي لتخطي نظام الاستضافة وإبقاء البوت حياً مجاناً
app = Flask(__name__)

@app.route('/')
def home():
    return "سلايدز بوت المحصن بقاعدة بيانات يعمل بنجاح!"

# 🔑 بياناتك الثابتة والمدمجة:
BOT_TOKEN = "8568933769:AAGPBh4YytR_K0HzVwUfDMhDSbX7Di57dtY"
OWNER_ID = 995412569  # حساب منصور المالك الأسطوري

# 🗃️ اسم ملف حفظ المشتركين دائمًا على السيرفر
DB_FILE = "database.txt"

# دالة لقراءة المشتركين من الملف عند تشغيل السيرفر
def load_subscribers():
    subs = {OWNER_ID: "permanent"} # منصور مضاف دائماً كمالك
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line:
                    continue
                uid_str, exp_str = line.split(",")
                try:
                    uid = int(uid_str)
                    if exp_str == "permanent":
                        subs[uid] = "permanent"
                    else:
                        subs[uid] = datetime.strptime(exp_str, "%Y-%m-%d %H:%M:%S")
                except:
                    continue
    return subs

# دالة لحفظ المشتركين داخل الملف فور تعديلهم
def save_subscribers():
    with open(DB_FILE, "w") as f:
        for uid, exp in SUBSCRIBERS.items():
            if exp == "permanent":
                f.write(f"{uid},permanent\n")
            else:
                f.write(f"{uid},{exp.strftime('%Y-%m-%d %H:%M:%S')}\n")

# تحميل قاعدة البيانات فوراً في الذاكرة عند الإقلاع
SUBSCRIBERS = load_subscribers()

# مخزن مؤقت لحفظ رقم الـ ID الذي تريد إضافته أثناء المحادثة
admin_state = {}

bot = telebot.TeleBot(BOT_TOKEN)

# --- دالة التحقق من حالة الاشتراك والمدة ---
def check_subscription(user_id):
    if user_id == OWNER_ID:
        return True, "اشتراك دائم (المالك)"
    
    if user_id in SUBSCRIBERS:
        exp_time = SUBSCRIBERS[user_id]
        if exp_time == "permanent":
            return True, "مدى الحياة ✨"
        
        # التحقق إذا كان الاشتراك لا يزال سارياً
        if datetime.now() < exp_time:
            remaining = exp_time - datetime.now()
            days = remaining.days
            hours = remaining.seconds // 3600
            return True, f"مفعل (متبقي {days} يوم و {hours} ساعة)"
        else:
            # منتهي الصلاحية، يتم حذفه من الذاكرة والملف تلقائياً
            del SUBSCRIBERS[user_id]
            save_subscribers()
            return False, "منتهي"
            
    return False, "غير مشترك"

# --- دالة الذكاء الاصطناعي للتلخيص ---
def ai_summarize(text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer sk-or-v1-7394627409284719384729183471928347192834", 
        "Content-Type": "application/json"
    }
    prompt = (
        f"أنت المساعد الدراسي الذكي 'سلايدز بوت'. قم بتحليل النص التالي وتلخيصه وترجمته إلى لغة عربية مفهومة للطلاب مع الحفاظ على المصطلحات الطبية والعلمية بالإنجليزية بين أقواس.\n"
        f"1. 💡 الخلاصة السريعة.\n"
        f"2. 📌 النقاط الرئيسية المهمة للاختبار.\n"
        f"3. ❓ سؤالين امتحانات خيارات (MCQ) مع تحديد الإجابة الصحيحة.\n\nالنص:\n{text}"
    )
    payload = {
        "model": "google/gemma-2-9b-it:free", 
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except:
        pass
    return "📚 عذراً، السيرفر مشغول حالياً. الرجاء المحاولة مرة أخرى بعد دقيقة."

# --- الكيبورد الرئيسي ---
def main_keyboard(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    btn_usage = types.KeyboardButton("💡 كيف يخدمك سلايدز بوت؟")
    btn_status = types.KeyboardButton("📊 فحص اشتراكي")
    markup.add(btn_usage, btn_status)
    
    if user_id == OWNER_ID:
        btn_admin = types.KeyboardButton("👑 لوحة تحكم المالك")
        markup.add(btn_admin)
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = message.from_user.id
    welcome_msg = (
        "🔥 أهلاً بك في **سلايدز بوت | Slides Bot** الأسطوري! 🎓\n\n"
        "انسخ نص أي سلايد أو محاضرة معقدة وأرسلها لي هنا، وسأقوم فوراً بتلخيصها وترجمتها واستخراج الأسئلة المتوقعة! 🚀"
    )
    bot.send_message(user_id, welcome_msg, reply_markup=main_keyboard(user_id), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_bot_logic(message):
    user_id = message.from_user.id
    text = message.text

    if text == "💡 كيف يخدمك سلايدز بوت?":
        guide = "🤖 **خدمات سلايدز بوت:**\n1. تلخيص السلايدات الطبية والعلمية.\n2. تحويل التعقيد لنقاط مراجعة.\n3. صناعة أسئلة امتحانات (MCQ).\n\n📝 انسخ أي نص وأرسله لي مباشرة."
        bot.send_message(user_id, guide)
        return

    if text == "📊 فحص اشتراكي":
        is_active, status_msg = check_subscription(user_id)
        bot.send_message(user_id, f"👤 **حالة حسابك حالياً:**\n🏷️ الميزة: {status_msg}\n🆔 الآي دي الخاص بك: `{user_id}`", parse_mode="Markdown")
        return

    if text == "👑 لوحة تحكم المالك" and user_id == OWNER_ID:
        admin_markup = types.InlineKeyboardMarkup(row_width=1)
        btn_add = types.InlineKeyboardButton("➕ إضافة مشترك جديد", callback_data="admin_add_user")
        btn_list = types.InlineKeyboardButton("📋 عرض كل المشتركين", callback_data="admin_list_users")
        admin_markup.add(btn_add, btn_list)
        bot.send_message(user_id, "⚙️ **أهلاً بك يا قائد في لوحة التحكم السرية:**", reply_markup=admin_markup)
        return

    if user_id == OWNER_ID and admin_state.get(user_id) == "waiting_for_id":
        try:
            target_id = int(text)
            admin_state[user_id] = {"target_id": target_id}
            
            duration_markup = types.InlineKeyboardMarkup(row_width=1)
            duration_markup.add(
                types.InlineKeyboardButton("⏱️ تجربة (يوم واحد)", callback_data="time_1_day"),
                types.InlineKeyboardButton("📅 شهر كامل (30 يوم)", callback_data="time_30_days"),
                types.InlineKeyboardButton("👑 دائم مدى الحياة", callback_data="time_permanent")
            )
            bot.send_message(user_id, f"📥 تم استلام الآي دي: `{target_id}`\n\nقم باختيار مدة الاشتراك المفضلة لهذا الطالب:", reply_markup=duration_markup, parse_mode="Markdown")
        except ValueError:
            bot.send_message(user_id, "❌ خطأ! يرجى إرسال أرقام فقط.")
        return

    is_active, status_msg = check_subscription(user_id)
    if not is_active:
        not_sub_msg = (
            "❌ **عذراً، اشتراكك في سلايدز بوت غير مفعل حالياً!**\n\n"
            "للاشتراك بسعر رمزي بسيط والاستفادة من ميزات التلخيص اللانهائية وصناعة الأسئلة، "
            "يرجى التواصل مع إدارة البوت لشحن حسابك.\n\n"
            f"🆔 معرف الحساب الخاص بك (انسخه وأرسله للموزع): `{user_id}`"
        )
        bot.send_message(user_id, not_sub_msg, parse_mode="Markdown")
        return

    bot.send_message(user_id, "⚡ جاري معالجة وتلخيص السلايد عبر ذكاء بايثون...")
    summary_result = ai_summarize(text)
    bot.send_message(user_id, summary_result, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    
    if user_id != OWNER_ID:
        return

    if call.data == "admin_add_user":
        admin_state[user_id] = "waiting_for_id"
        bot.edit_message_text("📥 ممتاز، أرسل لي الآن رقم الـ ID الخاص بالطالب المراد تفعيله مباشرة في الشات:", chat_id=call.message.chat.id, message_id=call.message.message_id)
        
    elif call.data == "admin_list_users":
        list_msg = "📋 **قائمة المشتركين الحاليين المحفوظة:**\n\n"
        for uid, exp in SUBSCRIBERS.items():
            if exp == "permanent":
                list_msg += f"• `{uid}` ➡️ دائم 👑\n"
            else:
                list_msg += f"• `{uid}` ➡️ ينتهي بتاريخ: {exp.strftime('%Y-%m-%d')}\n"
        bot.edit_message_text(list_msg, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")

    elif call.data.startswith("time_"):
        if user_id in admin_state and isinstance(admin_state[user_id], dict):
            target_id = admin_state[user_id]["target_id"]
            action = call.data
            
            if action == "time_1_day":
                SUBSCRIBERS[target_id] = datetime.now() + timedelta(days=1)
                duration_text = "يوم واحد (تجريبي)"
            elif action == "time_30_days":
                SUBSCRIBERS[target_id] = datetime.now() + timedelta(days=30)
                duration_text = "شهر كامل (30 يوم)"
            elif action == "time_permanent":
                SUBSCRIBERS[target_id] = "permanent"
                duration_text = "مدى الحياة دائم 👑"
                
            # حفظ التحديثات فورًا في ملف التخزين الدائم
            save_subscribers()
            
            bot.edit_message_text(f"✅ **تم التفعيل وباقي محفوظ في ملفك للأبد!**\n\n👤 الحساب: `{target_id}`\n⏱️ المدة: {duration_text}", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
            
            try:
                bot.send_message(target_id, f"🎉 **مبـروك! تم تفعيل اشتراكك في سلايدز بوت بنجاح!**\n⏱️ مدة اشتراكك: {duration_text}\n\nابدأ الآن بإرسال نصوص السلايدات والمحاضرات لتلخيصها فوراً! 🚀")
            except:
                pass
            
            del admin_state[user_id]

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    print("[*] 🎓 سلايدز بوت الاحترافي يعمل الآن بقاعدة بيانات كاملة...")
    bot.infinity_polling()
