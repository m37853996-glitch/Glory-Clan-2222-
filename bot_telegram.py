import os
import json
import subprocess
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

TOKEN = "9249471028:AAF465dw_hyTiVOq4cWpKlWSexqZi6DxZUo"
ADMIN_ID = 8988529781  # المطور الأساسي

DATA_FILE = "bot_data.json"
ACCOUNTS_FILE = "accounts.json"  # ملف الحسابات الحقيقي
CONFIG_FILE = "config_runtime.json"  # ملف تمرير الإعدادات للسكربت الفعلي
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

# دالة تشغيل السكربت الفعلي وتمرير بيانات الحسابات والكلان الحقيقي للعبة
def manage_script_execution():
    global bot_process
    while True:
        data = load_data()
        if data["bot_status"] == "ON":
            if bot_process is None or bot_process.poll() is not None:
                script_to_run = "main.py"  # سكربت فري فاير الأساسي
                if os.path.exists(script_to_run):
                    # حفظ إعدادات التشغيل الحالية لكي يقرأها main.py (الكلان، السكوادات، والحسابات)
                    runtime_config = {
                        "target_clan": data.get("target_clan"),
                        "max_squads": data.get("max_squads", 5),
                        "status": "RUNNING"
                    }
                    with open(CONFIG_FILE, "w", encoding="utf-8") as cf:
                        json.dump(runtime_config, cf, ensure_ascii=False, indent=4)

                    print(f"Starting Free Fire script {script_to_run} with target clan & accounts...")
                    # تشغيل السكربت الفعلي مع تمرير الملفات المطلوبة
                    bot_process = subprocess.Popen(["python", script_to_run])
        else:
            if bot_process is not None and bot_process.poll() is None:
                print("Stopping Free Fire script execution...")
                bot_process.terminate()
                bot_process = None
                # تحديث ملف الإيقاف
                if os.path.exists(CONFIG_FILE):
                    try:
                        with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
                            cfg = json.load(cf)
                        cfg["status"] = "STOPPED"
                        with open(CONFIG_FILE, "w", encoding="utf-8") as cf:
                            json.dump(cfg, cf, ensure_ascii=False, indent=4)
                    except:
                        pass
        time.sleep(5)

threading.Thread(target=manage_script_execution, daemon=True).start()

def check_updates():
    offset = 0
    print("Bot polling started with full Free Fire execution integration...")
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
                            user_id = str(message["from"]["id"])
                            text = message.get("text", "").strip()
                            
                            data = load_data()
                            
                            # قراءة عدد الحسابات من ملف accounts.json الحقيقي
                            accounts_count = 0
                            if os.path.exists(ACCOUNTS_FILE):
                                try:
                                    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                                        acc_data = json.load(f)
                                        accounts_count = len(acc_data) if isinstance(acc_data, list) else 0
                                except:
                                    pass

                            if text == "/start" or text == "القائمة الرئيسية":
                                status_text = "🟢 شغال (يسجل دخول وينفذ باللعبة)" if data["bot_status"] == "ON" else "🔴 مطفأ"
                                clan_id = data.get("target_clan", "⚠️ غير محدد (الرجاء إضافته)")
                                max_squads = data.get("max_squads", 5)
                                
                                menu_text = (
                                    f"🔥 لوحة تحكم Free Fire الحقيقية:\n\n"
                                    f"• حالة الاتصال باللعبة: {status_text}\n"
                                    f"• الحسابات المحملة بالملف: {accounts_count} حساب\n"
                                    f"• أيدي الكلان المستهدف: {clan_id}\n"
                                    f"• السكوادات المحددة لكل كلان: {max_squads}\n\n"
                                    f"اختر من الأزرار للتحكم الفعلي:"
                                )
                                
                                keyboard = {
                                    "keyboard": [
                                        [{"text": "تشغيل الحسابات والكلان 🟢"}, {"text": "إطفاء الحسابات 🔴"}],
                                        [{"text": "➕ إضافة أيدي كلان"}, {"text": "🎯 تحديد عدد السكوادات"}],
                                        [{"text": "📋 حالة الحسابات والكلان"}, {"text": "🔄 تحديث"}]
                                    ],
                                    "resize_keyboard": True
                                }
                                send_message(chat_id, menu_text, keyboard)
                            
                            elif text == "تشغيل الحسابات والكلان 🟢":
                                if not data.get("target_clan"):
                                    send_message(chat_id, "⚠️ تنبيه: يرجى إضافة أيدي الكلان أولاً عبر زر (➕ إضافة أيدي كلان) لكي تعرف الحسابات أين تنضم!")
                                    continue
                                
                                data["bot_status"] = "ON"
                                save_data(data)
                                send_message(chat_id, "🚀 تم إرسال أمر التشغيل! السكربت بدأ الآن بقراءة الحسابات وتسجيل الدخول وتوجيهها لدخول الكلان في فري فاير...")
                                
                            elif text == "إطفاء الحسابات 🔴":
                                data["bot_status"] = "OFF"
                                save_data(data)
                                send_message(chat_id, "🛑 تم إيقاف السكربت وتسجيل الخروج.")
                                
                            elif text == "➕ إضافة أيدي كلان":
                                send_message(chat_id, "أرسل أيدي الكلان المراد دخول الحسابات إليه هكذا:\n`/setclan [الأيدي]`\nمثال: `/setclan 8429341771`")
                                
                            elif text.startswith("/setclan "):
                                clan_id = text.replace("/setclan", "").strip()
                                if clan_id:
                                    data["target_clan"] = clan_id
                                    save_data(data)
                                    send_message(chat_id, f"✅ تم حفظ أيدي الكلان المستهدف ({clan_id}) بنجاح!")

                            elif text == "🎯 تحديد عدد السكوادات":
                                send_message(chat_id, "أرسل عدد السكوادات هكذا:\n`/setsquad [الرقم]`\nمثال: `/setsquad 4`")

                            elif text.startswith("/setsquad "):
                                try:
                                    num = int(text.replace("/setsquad", "").strip())
                                    data["max_squads"] = num
                                    save_data(data)
                                    send_message(chat_id, f"🎯 تم ضبط عدد السكوادات إلى: {num}")
                                except:
                                    send_message(chat_id, "❌ خطأ، أرسل رقماً صحيحاً.")

                            elif text == "📋 حالة الحسابات والكلان":
                                clan_id = data.get("target_clan", "غير محدد")
                                squads = data.get("max_squads", 5)
                                send_message(chat_id, f"📊 التقرير الفعلي:\n- الحسابات الجاهزة: {accounts_count}\n- الكلان: {clan_id}\n- السكوادات: {squads}")

                            elif text == "🔄 تحديث":
                                send_message(chat_id, "🔄 تم التحديث.")
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    check_updates()
