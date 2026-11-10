import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- إعدادات البوت الأساسية ---
TOKEN = "9249471028:AAF465dw_hyTiVOq4cWpKlWSexqZi6DxZUo"
ADMIN_ID = 8988529781  # الأيدي الخاص بك

# --- سيرفر الويب الوهمي للحفاظ على نشاط Render 24/7 ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# تشغيل السيرفر في الخلفية
threading.Thread(target=run_web_server, daemon=True).start()
# --------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("عذراً، هذا البوت خاص بالمطور فقط.")
        return
    
    await update.message.reply_text("أهلاً بك يا مطورنا! بوت إدارة حسابات Free Fire يعمل الآن بنجاح 24/7 🚀")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    
    print("Bot is starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
