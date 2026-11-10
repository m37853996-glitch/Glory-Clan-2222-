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
        "users_data": {},     # تخزين بيانات كل مستخدم حسب الأيدي (حسابات، كلانات، سكوادات)
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

# دالة تشغيل السكربت الفعلي في الخلفية للمستخدمين
def manage_script_execution():
    global bot_process
    while True:
        data = load_data()
        # التحقق مما إذا كان هناك أي مستخدم مفعل لديه الحسابات والتشغيل
        any_active = any(u.get("status") == "ON" for u in data.get("users_data", {}).values())
        
        if any_active:
            if bot_process is None or bot_process.poll() is not None:
                script_to_run = "main.py"
                if os.path.exists(script_to_run):
                    print(f"Starting script {script_to_run} for user accounts...")
                    bot_process = subprocess.Popen(["python", script_to_run])
        else:
            if bot_process is not None and bot_process.poll() is None:
                print("Stopping script execution...")
                bot_process.terminate()
                bot_process = None
        time.sleep(5)

threading.Thread(target=manage_script_execution, daemon=True).start()

def check_updates():
    offset = 0
    print("Bot polling started with user-based multi-account & squad management...")
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
                            admins = [str(a) for a in data.get("admins", [ADMIN_ID])]
                            
                            # التحقق من صلاحية الوصول (مدفوع / مطور)
                            if user_id not in admins and len(admins) > 0:
                                # إذا أردت السماح لأي شخص بالدفع أو التجربة، أو قصرها على المطورين
                                pass
                            
                            # تهيئة بيانات المستخدم الشخصية إذا لم تكن موجودة
                            if user_id not in data["users_data"]:
                                data["users_data"][user_id] = {
                                    "status": "OFF",
                                    "clans": [],
                                    "accounts": [],
                                    "max_squads": 1
                                }
                                save_data(data)
                            
                            user_info = data["users_data"][user_id]
                            
                            if text == "/start" or text == "القائمة الرئيسية":
                                status_text = "🟢 شغال" if user_info["status"] == "ON" else "🔴 مطفأ"
                                clans_count = len(user_info["clans"])
                                accounts_count = len(user_info["accounts"])
                                max_squads = user_info["max_squads"]
                                
                                menu_text = (
                                    f" أهلاً بك في لوحة تحكم حساباتك الشخصية لـ Free Fire 🚀\n\n"
                                    f"• حالة حساباتك: {status_text}\n"
                                    f"• الحسابات المضافة: {accounts_count}\n"
                                    f"• الكلانات الخاصة بك: {clans_count}\n"
                                    f"• السكوادات لكل كلان: {max_squads}\n\n"
                                    f"اختر ما تريد من الأزرار بالأسفل:"
                                )
                                
                                keyboard = {
                                    "keyboard": [
                                        [{"text": "تشغيل حساباتي 🟢"}, {"text": "إطفاء حساباتي 🔴"}],
                                        [{"text": "➕ إضافة حسابات"}, {"text": "➕ إضافة أيدي كلان"}],
                                        [{"text": "🎯 تحديد عدد السكوادات"}, {"text": "📋 عرض بياناتي"}],
                                        [{"text": "➖ حذف كلان"}, {"text": "🔄 تحديث"}]
                                    ],
                                    "resize_keyboard": True
                                }
                                send_message(chat_id, menu_text, keyboard)
                            
                            elif text == "تشغيل حساباتي 🟢":
                                user_info["status"] = "ON"
                                save_data(data)
                                send_message(chat_id, "✅ تم تشغيل حساباتك وسكربتك الفعلي بنجاح! 🚀")
                                
                            elif text == "إطفاء حساباتي 🔴":
                                user_info["status"] = "OFF"
                                save_data(data)
                                send_message(chat_id, "🛑 تم إطفاء حساباتك وتوقف السكربت الخاص بك.")
                                
                            elif text == "➕ إضافة حسابات":
                                send_message(chat_id, "أرسل حساباتك أو ايديهات الحسابات بالشكل التالي:\n`/addacc [الحسابات / الإيديهات]`")

                            elif text.startswith("/addacc "):
                                acc_info = text.replace("/addacc", "").strip()
                                if acc_info:
                                    user_info["accounts"].append(acc_info)
                                    save_data(data)
                                    send_message(chat_id, f"✅ تم إضافة الحساب بنجاح! إجمالي حساباتك: {len(user_info['accounts'])}")

                            elif text == "➕ إضافة أيدي كلان":
                                send_message(chat_id, "أرسل أيدي الكلان الخاص بك هكذا:\n`/addclan [الإيدي]`")
                                
                            elif text.startswith("/addclan "):
                                clan_id = text.replace("/addclan", "").strip()
                                if clan_id:
                                    if clan_id not in user_info["clans"]:
                                        user_info["clans"].append(clan_id)
                                        save_data(data)
                                        send_message(chat_id, f"✅ تم إضافة أيدي الكلان ({clan_id}) لحسابك بنجاح!")
                                    else:
                                        send_message(chat_id, "⚠️ هذا الكلان مضاف مسبقاً لديك.")

                            elif text == "🎯 تحديد عدد السكوادات":
                                send_message(chat_id, "أرسل عدد السكوادات التي تريد دخولها للكلان هكذا:\n`/setsquad [الرقم]`\nمثال: `/setsquad 4`")

                            elif text.startswith("/setsquad "):
                                try:
                                    num = int(text.replace("/setsquad", "").strip())
                                    user_info["max_squads"] = num
                                    save_data(data)
                                    send_message(chat_id, f"🎯 تم تحديث عدد السكوادات لكل كلان إلى: {num}")
                                except:
                                    send_message(chat_id, "❌ خطأ، أرسل رقماً صحيحاً.")

                            elif text == "📋 عرض بياناتي":
                                clans = user_info["clans"]
                                accs = user_info["accounts"]
                                squads = user_info["max_squads"]
                                clans_str = "\n".join([f"- {c}" for c in clans]) if clans else "لا توجد كلانات."
                                send_message(chat_id, f"📊 بياناتك الشخصية:\n- عدد الحسابات: {len(accs)}\n- سكوادات الكلان: {squads}\n\n📋 كلاناتك:\n{clans_str}")

                            elif text == "➖ حذف كلان":
                                clans = user_info["clans"]
                                if not clans:
                                    send_message(chat_id, "ليس لديك كلانات لحذفها.")
                                else:
                                    clans_str = "\n".join([f"- {c}" for c in clans])
                                    send_message(chat_id, f"أرسل الأيدي الذي تريد حذفه هكذا:\n`/delclan [الإيدي]`\n\nكلاناتك الحالية:\n{clans_str}")

                            elif text.startswith("/delclan "):
                                clan_id = text.replace("/delclan", "").strip()
                                if clan_id in user_info["clans"]:
                                    user_info["clans"].remove(clan_id)
                                    save_data(data)
                                    send_message(chat_id, f"🗑️ تم حذف الكلان ({clan_id}) بنجاح.")
                                else:
                                    send_message(chat_id, "❌ الأيدي غير موجود في كلاناتك.")

                            elif text == "🔄 تحديث":
                                send_message(chat_id, "🔄 تم تحديث لوحتك بنجاح.")
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    check_updates()
