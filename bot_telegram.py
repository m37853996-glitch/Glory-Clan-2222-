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
bot_process = None  # متغير لتخزين عملية السكربت الشغال

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "admins": [ADMIN_ID],
        "clans": [],
        "max_squads": 5,      # عدد السكوادات الافتراضي
        "bot_status": "OFF",  # حالة التشغيل
        "is_paid": True       # وضع المدفوع
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

# دالة تشغيل السكربت الفعلي (مثل main.py أو سكربتات الحسابات والكلانات)
def manage_script_execution():
    global bot_process
    while True:
        data = load_data()
        if data["bot_status"] == "ON":
            if bot_process is None or bot_process.poll() is not None:
                # هنا يتم تشغيل السكربت الحقيقي الخاص بك (مثال: main.py)
                script_to_run = "main.py"  # يمكنك تغيير اسم الملف إذا أردت
                if os.path.exists(script_to_run):
                    print(f"Starting script {script_to_run}...")
                    bot_process = subprocess.Popen(["python", script_to_run])
        else:
            if bot_process is not None and bot_process.poll() is None:
                print("Stopping script execution...")
                bot_process.terminate()
                bot_process = None
        time.sleep(5)

# تشغيل مراقب السكربت في الخلفية
threading.Thread(target=manage_script_execution, daemon=True).start()

def check_updates():
    offset = 0
    print("Bot polling started with direct script execution...")
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
                            
                            if user_id not in admins:
                                send_message(chat_id, "عذراً، هذا البوت مدفوع ومخصص للمطورين المعتمدين فقط 🔒")
                                continue
                            
                            if text == "/start" or text == "القائمة الرئيسية":
                                status_text = "🟢 شغال" if data["bot_status"] == "ON" else "🔴 مطفأ"
                                clans_count = len(data["clans"])
                                max_squads = data.get("max_squads", 5)
                                
                                menu_text = (
                                    f"أهلاً بك يا مطورنا في لوحة تحكم السكربتات 🚀\n\n"
                                    f"• حالة تشغيل السكربت: {status_text}\n"
                                    f"• عدد الكلانات المضافة: {clans_count}\n"
                                    f"• عدد السكوادات لكل كلان: {max_squads}\n\n"
                                    f"اختر ما تريد من الأزرار بالأسفل:"
                                )
                                
                                keyboard = {
                                    "keyboard": [
                                        [{"text": "تشغيل الحسابات 🟢"}, {"text": "إطفاء الحسابات 🔴"}],
                                        [{"text": "➕ إضافة أيدي كلان"}, {"text": "➖ حذف أيدي كلان"}],
                                    [{"text": "📋 عرض الكلانات"}, {"text": "🎯 تحديد عدد السكوادات"}],
                                        [{"text": "➕ إضافة مطور (أيدي)"}, {"text": "🔄 تحديث الحالة"}]
                                    ],
                                    "resize_keyboard": True
                                }
                                send_message(chat_id, menu_text, keyboard)
                            
                            elif text == "تشغيل الحسابات 🟢":
                                data["bot_status"] = "ON"
                                save_data(data)
                                send_message(chat_id, "✅ تم تفعيل تشغيل السكربت والحسابات الفعلية بنجاح! 🚀")
                                
                            elif text == "إطفاء الحسابات 🔴":
                                data["bot_status"] = "OFF"
                                save_data(data)
                                send_message(chat_id, "🛑 تم إطفاء السكربت وإيقاف الحسابات بنجاح.")
                                
                            elif text == "📋 عرض الكلانات":
                                clans = data.get("clans", [])
                                max_squads = data.get("max_squads", 5)
                                if not clans:
                                    send_message(chat_id, "لا توجد أي كلانات مضافة حالياً.")
                                else:
                                    clans_str = "\n".join([f"- {c}" for c in clans])
                                    send_message(chat_id, f"📋 قائمة كلانات Free Fire المضافة (السكوادات: {max_squads}):\n\n{clans_str}")
                                    
                            elif text.startswith("➕ إضافة أيدي كلان"):
                                send_message(chat_id, "أرسل الآن أيدي الكلان بالشكل التالي:\n`/addclan [الإيدي]`")
                                
                            elif text.startswith("/addclan "):
                                clan_id = text.replace("/addclan", "").strip()
                                if clan_id:
                                    if clan_id not in data["clans"]:
                                        data["clans"].append(clan_id)
                                        save_data(data)
                                        send_message(chat_id, f"✅ تم إضافة أيدي الكلان ({clan_id}) وتفعيله بالسكربت!")
                                    else:
                                        send_message(chat_id, "⚠️ هذا الكلان مضاف مسبقاً.")
                                        
                            elif text.startswith("➖ حذف أيدي كلان"):
                                clans = data.get("clans", [])
                                if not clans:
                                    send_message(chat_id, "لا توجد كلانات لحذفها.")
                                else:
                                    clans_str = "\n".join([f"- {c}" for c in clans])
                                    send_message(chat_id, f"أرسل الأيدي الذي تريد حذفه هكذا:\n`/delclan [الإيدي]`\n\nالكلانات الحالية:\n{clans_str}")
                                    
                            elif text.startswith("/delclan "):
                                clan_id = text.replace("/delclan", "").strip()
                                if clan_id in data["clans"]:
                                    data["clans"].remove(clan_id)
                                    save_data(data)
                                    send_message(chat_id, f"🗑️ تم حذف الكلان ({clan_id}) بنجاح.")
                                else:
                                    send_message(chat_id, "❌ الأيدي غير موجود في القائمة.")

                            elif text.startswith("🎯 تحديد عدد السكوادات"):
                                send_message(chat_id, "أرسل الأمر مع العدد الجديد هكذا:\n`/setsquad [الرقم]`\nمثال: `/setsquad 4`")

                            elif text.startswith("/setsquad "):
                                try:
                                    num = int(text.replace("/setsquad", "").strip())
                                    data["max_squads"] = num
                                    save_data(data)
                                    send_message(chat_id, f"🎯 تم تحديث عدد السكوادات لكل كلان إلى: {num}")
                                except:
                                    send_message(chat_id, "❌ خطأ، أرسل رقماً صحيحاً.")
                                    
                            elif text.startswith("➕ إضافة مطور (أيدي)"):
                                send_message(chat_id, "أرسل أيدي المطور الجديد هكذا:\n`/addadmin [الأيدي]`")
                                
                            elif text.startswith("/addadmin "):
                                try:
                                    new_admin = int(text.replace("/addadmin", "").strip())
                                    if new_admin not in data["admins"]:
                                        data["admins"].append(new_admin)
                                        save_data(data)
                                        send_message(chat_id, f"👑 تم إضافة المطور الجديد بالأيدي ({new_admin}) بنجاح!")
                                    else:
                                        send_message(chat_id, "⚠️ هذا المستخدم مطور بالفعل.")
                                except:
                                    send_message(chat_id, "❌ أيدي غير صالح.")
                                    
                            elif text == "🔄 تحديث الحالة":
                                status_text = "🟢 شغال" if data["bot_status"] == "ON" else "🔴 مطفأ"
                                max_squads = data.get("max_squads", 5)
                                send_message(chat_id, f"حالة السكربت: {status_text} | السكوادات: {max_squads}")
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    check_updates()

