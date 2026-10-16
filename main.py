import time
import requests

# ==================== الثوابت ====================
TELEGRAM_BOT_TOKEN = "8498358854:AAHnd7NS_bbSWUI8pFu8kGpsgChH_pWqEQM"
TELEGRAM_CHAT_ID = "7622929642"
CHECK_INTERVAL = 60  # الفترة الزمنية بالثواني (60 ثانية = دقيقة واحدة)
# ====================================================

def send_telegram_message(message):
    """دالة لإرسال إشعار عبر بوت التليجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"[-] خطأ في إرسال رسالة التليجرام: {e}")
        return False

def check_tiktok_user(username):
    """دالة للتحقق من وجود حساب تيك توك"""
    url = f"https://www.tiktok.com/@{username}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            if "Couldn't find this account" not in response.text and "couldn't find this account" not in response.text.lower():
                return True
        return False
    except Exception as e:
        print(f"[-] خطأ أثناء الاتصال بتيك توك: {e}")
        return False

def main():
    # طلب اسم المستخدم من المستخدم عند تشغيل السكريبت
    target_username = input("أدخل اسم المستخدم الذي تريد مراقبته (بدون @): ").strip()
    
    if not target_username:
        print("[-] لم تقم بإدخال أي اسم مستخدم. تم إيقاف البرنامج.")
        return

    print(f"\n[*] بدء مراقبة الحساب: @{target_username} (كل {CHECK_INTERVAL} ثانية)...\n")
    
    while True:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] جاري التحقق من الحساب...")
        
        exists = check_tiktok_user(target_username)
        
        if exists:
            message = (
                f"🎯 **تم العثور على الحساب!**\n\n"
                f"👤 **اسم المستخدم:** `@{target_username}`\n"
                f"🔗 **الرابط:** https://www.tiktok.com/@{target_username}\n"
                f"⏰ **التوقيت:** {timestamp}"
            )
            print("[+] تم العثور على الحساب! جاري إرسال الإشعار إلى تليجرام...")
            send_telegram_message(message)
            
            # إنهاء البرنامج بعد العثور عليه
            break
        else:
            print("[-] الحساب غير موجود حالياً. انتظار الدقيقة القادمة...")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
import time
import threading
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== الإعدادات الثابتة ====================
TELEGRAM_BOT_TOKEN = "8498358854:AAHnd7NS_bbSWUI8pFu8kGpsgChH_pWqEQM"
DEFAULT_INTERVAL = 60  # الفاصل الزمني الافتراضي بالثواني
# ====================================================

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# قاموس لتتبع حالة المراقبة لكل مستخدم تليجرام
# Structure: {chat_id: {"is_running": bool, "usernames": [], "interval": int, "continuous": bool}}
active_monitors = {}

def check_tiktok_user(username):
    """دالة للتحقق من وجود حساب تيك توك"""
    url = f"https://www.tiktok.com/@{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            if "Couldn't find this account" not in response.text and "couldn't find this account" not in response.text.lower():
                return True
        return False
    except Exception:
        return False

def monitor_loop(chat_id):
    """حلقة المراقبة التي تعمل في الخلفية"""
    while active_monitors.get(chat_id, {}).get("is_running", False):
        user_data = active_monitors.get(chat_id)
        if not user_data:
            break
            
        usernames = user_data["usernames"]
        interval = user_data["interval"]
        continuous = user_data["continuous"]
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        for username in usernames[:]:
            if not active_monitors.get(chat_id, {}).get("is_running", False):
                break
                
            exists = check_tiktok_user(username)
            
            if exists:
                mode_text = "🔄 (بحث متواصل مفعل)" if continuous else "⏹️ (تم إيقافه تلقائياً)"
                message = (
                    f"🎯 **تم العثور على الحساب!** {mode_text}\n\n"
                    f"👤 **اسم المستخدم:** `@{username}`\n"
                    f"🔗 **الرابط:** https://www.tiktok.com/@{username}\n"
                    f"⏰ **التوقيت:** {timestamp}"
                )
                bot.send_message(chat_id, message, parse_mode="Markdown")
                
                # إذا لم يكن وضع البحث المتواصل مفعلاً، نزيل الحساب أو نوقف المراقبة
                if not continuous:
                    usernames.remove(username)
                    if not usernames:
                        active_monitors[chat_id]["is_running"] = False
                        bot.send_message(chat_id, "🏁 انتهت المراقبة بنجاح.")
                        break
        
        if not active_monitors.get(chat_id, {}).get("is_running", False):
            break
            
        # الانتظار للفترة الزمنية المحددة مع مراعاة الإيقاف الفوري
        for _ in range(interval):
            if not active_monitors.get(chat_id, {}).get("is_running", False):
                break
            time.sleep(1)

def get_main_menu_keyboard(chat_id):
    """إنشاء لوحة مفاتيح تفاعلية لعرض الخيارات والتحكم"""
    markup = InlineKeyboardMarkup()
    monitor = active_monitors.get(chat_id, {})
    is_running = monitor.get("is_running", False)
    continuous = monitor.get("continuous", False)
    
    if is_running:
        markup.add(InlineKeyboardButton("🛑 إيقاف المراقبة", callback_data="stop_bot"))
    else:
        markup.add(InlineKeyboardButton("🚀 بدء مراقبة جديدة", callback_data="help_check"))
        
    cont_text = "✅ البحث المتواصل: مفعل" if continuous else "❌ البحث المتواصل: معطل"
    markup.add(InlineKeyboardButton(cont_text, callback_data="toggle_continuous"))
    markup.add(InlineKeyboardButton("📊 الحالة الحالية", callback_data="status_bot"),
               InlineKeyboardButton("⚙️ طريقة الاستخدام", callback_data="help_menu"))
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    text = (
        "🤖 **أهلاً بك في لوحة تحكم بوت تيك توك المتقدمة!**\n\n"
        "يمكنك التحكم بكافة الخيارات عبر الأوامر أو باستخدام الأزرار أدناه 👇:\n\n"
        "🔹 `/check user1, user2` - لمراقبة حسابات.\n"
        "🔹 `/continuous` - تفعيل/تعطيل البحث المتواصل.\n"
        "🔹 `/status` - عرض الحالة.\n"
        "🔹 `/stop` - إيقاف."
    )
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    
    if data == "stop_bot":
        if chat_id in active_monitors:
            active_monitors[chat_id]["is_running"] = False
        bot.answer_callback_query(call.id, "🛑 تم إيقاف المراقبة.")
        bot.edit_message_text("🛑 **تم إيقاف المراقبة بنجاح.**", chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
        
    elif data == "status_bot":
        monitor = active_monitors.get(chat_id)
        if monitor and monitor.get("is_running", False):
            users = ", ".join([f"`@{u}`" for u in monitor['usernames']])
            cont = "مفعل (يستمر بالفحص حتى لو وجد الحساب)" if monitor['continuous'] else "معطل (يتوقف عند إيجاده)"
            text = f"🟢 **البوت يعمل حالياً!**\n\n📋 الحسابات: {users}\n⏱️ السرعة: {monitor['interval']}ث\n🔄 البحث المتواصل: {cont}"
        else:
            text = "🔴 **البوت متوقف حالياً ولا توجد مراقبة نشطة.**"
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
        
    elif data == "toggle_continuous":
        if chat_id not in active_monitors:
            active_monitors[chat_id] = {"is_running": False, "usernames": [], "interval": DEFAULT_INTERVAL, "continuous": True}
        else:
            active_monitors[chat_id]["continuous"] = not active_monitors[chat_id].get("continuous", False)
        
        status_state = "مفعل 🟢" if active_monitors[chat_id]["continuous"] else "معطل 🔴"
        bot.answer_callback_query(call.id, f"تم تغيير وضع البحث المتواصل إلى: {status_state}")
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_main_menu_keyboard(chat_id))
        
    elif data == "help_check":
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, "✍️ لبدء المراقبة، أرسل الأمر بالشكل التالي:\n`/check username1, username2`", parse_mode="Markdown")
        
    elif data == "help_menu":
        bot.answer_callback_query(call.id)
        help_desc = (
        "⚙️ **دليل الخيارات:**\n"
        "1️⃣ **البحث المتواصل:** إذا كان مفعلاً، فلن يتوقف البوت عند إيجاد الحساب بل سيستمر في إرسال التنبيهات كل دقيقة للتأكد من أنه لا يزال متاحاً.\n"
        "2️⃣ **الأوامر النصية المتاحة:**\n"
        "• `/check <users>`\n• `/interval <seconds>`\n• `/continuous`\n• `/status`\n• `/stop`"
        )
        bot.send_message(chat_id, help_desc, parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))

@bot.message_handler(commands=['continuous'])
def toggle_continuous_command(message):
    chat_id = message.chat.id
    if chat_id not in active_monitors:
        active_monitors[chat_id] = {"is_running": False, "usernames": [], "interval": DEFAULT_INTERVAL, "continuous": True}
    else:
        active_monitors[chat_id]["continuous"] = not active_monitors[chat_id].get("continuous", False)
        
    state = "مفعل ✅" if active_monitors[chat_id]["continuous"] else "معطل ❌"
    bot.reply_to(message, f"🔄 تم تحديث خاصية **البحث المتواصل** لتصبح: **{state}**", parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))

@bot.message_handler(commands=['check'])
def start_monitoring(message):
    chat_id = message.chat.id
    text_parts = message.text.split(maxsplit=1)
    
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ يرجى كتابة اسم حساب واحد على الأقل.\nمثال: `/check username1, username2`", parse_mode="Markdown")
        return
    
    raw_usernames = text_parts[1].split(',')
    usernames = [u.strip().replace("@", "") for u in raw_usernames if u.strip()]
    
    if not usernames:
        bot.reply_to(message, "⚠️ لم تقم بإدخال أسماء صحيحة.")
        return

    if active_monitors.get(chat_id, {}).get("is_running", False):
        bot.reply_to(message, "⚠️ لديك مراقبة نشطة بالفعل. أوقفها أولاً.", parse_mode="Markdown")
        return

    current_interval = active_monitors.get(chat_id, {}).get("interval", DEFAULT_INTERVAL)
    is_continuous = active_monitors.get(chat_id, {}).get("continuous", False)

    active_monitors[chat_id] = {
        "is_running": True,
        "usernames": usernames,
        "interval": current_interval,
        "continuous": is_continuous
    }
    
    formatted_list = "\n".join([f"• `@{u}`" for u in usernames])
    bot.reply_to(message, f"🚀 **بدأت المراقبة للحسابات:**\n{formatted_list}\n\n🔄 **البحث المتواصل:** {'مفعل' if is_continuous else 'معطل'}", parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
    
    monitor_thread = threading.Thread(target=monitor_loop, args=(chat_id,))
    monitor_thread.daemon = True
    monitor_thread.start()

@bot.message_handler(commands=['interval'])
def set_interval(message):
    chat_id = message.chat.id
    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2 or not text_parts[1].isdigit():
        bot.reply_to(message, "⚠️ مثال: `/interval 30`", parse_mode="Markdown")
        return
    new_interval = int(text_parts[1])
    if chat_id not in active_monitors:
        active_monitors[chat_id] = {"is_running": False, "usernames": [], "interval": new_interval, "continuous": False}
    else:
        active_monitors[chat_id]["interval"] = new_interval
    bot.reply_to(message, f"✅ تم تعيين الفاصل الزمني: كل {new_interval} ثانية.", reply_markup=get_main_menu_keyboard(chat_id))

@bot.message_handler(commands=['status'])
def check_status(message):
    chat_id = message.chat.id
    monitor = active_monitors.get(chat_id)
    if monitor and monitor.get("is_running", False):
        usernames = ", ".join([f"`@{u}`" for u in monitor['usernames']])
        cont = "مفعل" if monitor['continuous'] else "معطل"
        bot.reply_to(message, f"🟢 **البوت يعمل:**\n📋 الحسابات: {usernames}\n⏱️ السرعة: {monitor['interval']}ث\n🔄 البحث المتواصل: {cont}", parse_mode="Markdown", reply_markup=get_main_menu_keyboard(chat_id))
    else:
        bot.reply_to(message, "🔴 **لا توجد مراقبة نشطة حالياً.**", reply_markup=get_main_menu_keyboard(chat_id))

@bot.message_handler(commands=['stop'])
def stop_monitoring(message):
    chat_id = message.chat.id
    if chat_id in active_monitors:
        active_monitors[chat_id]["is_running"] = False
    bot.reply_to(message, "🛑 تم إيقاف المراقبة.", reply_markup=get_main_menu_keyboard(chat_id))

if __name__ == "__main__":
    print("[*] تم تشغيل البوت مع الأزرار التفاعلية والبحث المتواصل...")
    bot.infinity_polling()
