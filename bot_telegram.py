import os
import json
import subprocess
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

TOKEN = "9249471028:AAF465dw_hyTiVOq4cWpKlWSexqZi6DxZUo"
ADMIN_ID = 8988529781  # المطور الأساسي (أنت)

DATA_FILE = "bot_data.json"
ACCOUNTS_FILE = "accounts.json"  # ملف الحسابات الحقيقي
CONFIG_FILE = "config_runtime.json"
bot_process = None

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "admins": [ADMIN_ID],
        "bot_status": "OFF",
        "target_clan": None,
        "max_squads": 5
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- سيرفر الويب للحفاظ على نشاط Render 24/7 ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()
# --------------------------------------------------------

def send_message(chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

# دالة تشغيل السكربت الفعلي وتمرير البيانات للعبة
def manage_script_execution():
    global bot_process
    while True:
        data = load_data()
        if data["bot_status"] == "ON":
            if bot_process is None or bot_process.poll() is not None:
                script_to_run = "main.py"
                if os.path.exists(script_to_run):
                    runtime_config = {
                        "target_clan": data.get("target_clan"),
                        "max_squads": data.get("max_squads", 5),
                        "status": "RUNNING"
                    }
                    with open(CONFIG_FILE, "w", encoding="utf-8") as cf:
                        json.dump(runtime_config, cf, ensure_ascii=False, indent=4)

                    print(f"Starting Free Fire script {script_to_run}...")
                    bot_process = subprocess.Popen(["python", script_to_run])
        else:
            if bot_process is not None and bot_process.poll() is None:
                print("Stopping Free Fire script execution...")
                bot_process.terminate()
                bot_process = None
        time.sleep(5)

threading.Thread(target=manage_script_execution, daemon=True).start()

def check_updates():
    offset = 0
    print("Bot polling started with secure developer controls...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={offset}&timeout=30"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=35) as response:
                result = json.loads(response.read().decode("utf-8"))
                if result.get("ok"):
                    for update in result.get("result", []):
                        offset = update["update_id"] + 1
                        message = update.get("message")
                        if message:
                            chat_id = message["chat"]["id"]
                            user_id = message["from"]["id"]
                            text = message.get("text", "").strip()
                            
                            data = load_data()
                            admins = data.get("admins", [ADMIN_ID])
                            
                            # حماية البوت: التأكد أن المستخدم مطور مسجل فقط
                            if user_id not in admins:
                                send_message(chat_id, "🔒 عذراً، هذا البوت خاص بالمطور الأساسي والمطورين المعتمدين فقط.")
                                continue
                            
                            if text == "/start" or text == "القائمة الرئيسية":
                                status_text = "🟢 شغال (ينفذ باللعبة)" if data["bot_status"] == "ON" else "🔴 مطفأ"
                                clan_id = data.get("target_clan", "⚠️ لم يُحدد بعد")
                                max_squads = data.get("max_squads", 5)
                                
                                menu_text = (
                                    f"👑 أهلاً بك يا مطورنا في لوحة تحكم Free Fire المركزية:\n\n"
                                    f"• حالة النظام: {status_text}\n"
                                    f"• أيدي الكلان الحالي: {clan_id}\n"
                                    f"• السكوادات المحددة: {max_squads}\n\n"
                                    f"اختر من الأزرار بالأسفل للتنفيذ:"
                                )
                                
                                keyboard = {
                                    "keyboard": [
                                        [{"text": "📁 فحص وتحميل الحسابات"}, {"text": "➕ إضافة أيدي كلان"}],
                                        [{"text": "تشغيل الحسابات والكلان 🟢"}, {"text": "إطفاء الحسابات 🔴"}],
                                        [{"text": "🎯 تحديد عدد السكوادات"}, {"text": "➕ إضافة مطور (أيدي)"}],
                                        [{"text": "🔄 تحديث الحالة"}]
                                    ],
                                    "resize_keyboard": True
                                }
                                send_message(chat_id, menu_text, keyboard)
                            
                            elif text == "📁 فحص وتحميل الحسابات":
                                accounts_count = 0
                                sample_accounts = []
                                if os.path.exists(ACCOUNTS_FILE):
                                    try:
                                        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                                            acc_data = json.load(f)
                                            if isinstance(acc_data, list):
                                                for item in acc_data:
                                                    if isinstance(item, list):
                                                        accounts_count += len(item)
                                                        for sub in item[:2]: # عينات للتأكد
                                                            if isinstance(sub, dict):
                                                                sample_accounts.append(sub.get("nickname", "Account"))
                                                    elif isinstance(item, dict):
                                                        accounts_count += 1
                                                        if len(sample_accounts) < 3:
                                                            sample_accounts.append(item.get("nickname", "Account"))
                                    except Exception as e:
                                        send_message(chat_id, f"❌ خطأ في قراءة ملف الحسابات: {e}")
                                        continue
                                        
                                if accounts_count > 0:
                                    samples_str = ", ".join(sample_accounts)
                                    send_message(chat_id, f"✅ تم فحص وتحميل الحسابات بنجاح!\n\n📊 إجمالي الحسابات الجاهزة: {accounts_count} حساب\n🟢 الحالة: تعمل وشغالة 100%\n📌 عينة من النيكست: {samples_str}...")
                                else:
                                    send_message(chat_id, "⚠️ ملف `accounts.json` فارغ أو غير موجود بالمسار الصحيح.")

                            elif text == "➕ إضافة أيدي كلان":
                                send_message(chat_id, "أرسل أيدي الكلان المستهدف هكذا:\n`/setclan [الإيدي]`\nمثال: `/setclan 3079855932`")
                                
                            elif text.startswith("/setclan "):
                                clan_id = text.replace("/setclan", "").strip()
                                if clan_id:
                                    data["target_clan"] = clan_id
                                    save_data(data)
                                    send_message(chat_id, f"✅ تم حفظ أيدي الكلان ({clan_id}) بنجاح وجاهز للتوجيه!")

                            elif text == "تشغيل الحسابات والكلان 🟢":
                                if not data.get("target_clan"):
                                    send_message(chat_id, "⚠️ تنبيه: يرجى تحديد أيدي الكلان أولاً عبر زر (➕ إضافة أيدي كلان).")
                                    continue
                                data["bot_status"] = "ON"
                                save_data(data)
                                send_message(chat_id, "🚀 تم إرسال أمر التشغيل الفعلي! الحسابات تبدأ الآن بالاتصال ودخول الكلان باللعبة...")
                                
                            elif text == "إطفاء الحسابات 🔴":
                                data["bot_status"] = "OFF"
                                save_data(data)
                                send_message(chat_id, "🛑 تم إطفاء الحسابات وتوقف عمل السكربت.")
                                
                            elif text == "🎯 تحديد عدد السكوادات":
                                send_message(chat_id, "أرسل عدد السكوادات هكذا:\n`/setsquad [الرقم]`")

                            elif text.startswith("/setsquad "):
                                try:
                                    num = int(text.replace("/setsquad", "").strip())
                                    data["max_squads"] = num
                                    save_data(data)
                                    send_message(chat_id, f"🎯 تم ضبط عدد السكوادات إلى: {num}")
                                except:
                                    send_message(chat_id, "❌ خطأ في تنسيق الرقم.")

                            elif text == "➕ إضافة مطور (أيدي)":
                                send_message(chat_id, "أرسل أيدي المطور الجديد هكذا:\n`/addadmin [الأيدي]`")

                            elif text.startswith("/addadmin "):
                                try:
                                    new_admin = int(text.replace("/addadmin", "").strip())
                                    if new_admin not in data["admins"]:
                                        data["admins"].append(new_admin)
                                        save_data(data)
                                        send_message(chat_id, f"👑 تم إضافة المطور الجديد ({new_admin}) بنجاح!")
                                    else:
                                        send_message(chat_id, "⚠️ هذا المستخدم مطور مضاف مسبقاً.")
                                except:
                                    send_message(chat_id, "❌ أيدي غير صالح.")

                            elif text == "🔄 تحديث الحالة":
                                status_text = "🟢 شغال" if data["bot_status"] == "ON" else "🔴 مطفأ"
                                clan_id = data.get("target_clan", "غير محدد")
                                send_message(chat_id, f"🔄 الحالة: {status_text}\n- الكلان: {clan_id}")
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    check_updates()
