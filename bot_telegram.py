import os
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

TOKEN = "9249471028:AAF465dw_hyTiVOq4cWpKlWSexqZi6DxZUo"
ADMIN_ID = 8988529781

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

def send_message(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Error sending message: {e}")

def check_updates():
    offset = 0
    print("Bot polling started using pure HTTP requests...")
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
                            text = message.get("text", "")
                            
                            if user_id == ADMIN_ID:
                                if text == "/start":
                                    send_message(chat_id, "أهلاً بك يا مطورنا! بوت إدارة حسابات Free Fire يعمل الآن بنجاح تام 24/7 🚀")
                            else:
                                send_message(chat_id, "عذراً، هذا البوت خاص بالمطور فقط.")
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    check_updates()
