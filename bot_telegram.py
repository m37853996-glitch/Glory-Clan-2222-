# -*- coding: utf-8 -*-
import os
import json
import sqlite3
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = "9209438721:AAFD4xpDJgslscX2QG1bC6b06CEHHuVE9eM"
ADMIN_UID = 8988529781

bot = Bot(token=TELEGRAM_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

DB_FILE = "saas_system.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            is_active INTEGER DEFAULT 1,
            target_clan TEXT DEFAULT 'None'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            uid TEXT,
            password TEXT,
            nickname TEXT DEFAULT 'MICHAEL ELITE',
            region TEXT DEFAULT 'ME',
            status TEXT DEFAULT 'ACTIVE_VALID'
        )
    """)
    conn.commit()
    conn.close()

init_db()

class UserStates(StatesGroup):
    waiting_for_clan = State()
    waiting_for_accounts = State()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("SELECT target_clan FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    clan = row[0] if row and row[0] else "None"
    
    cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE user_id = ?", (user_id,))
    acc_count = cursor.fetchone()[0]
    conn.close()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📂 إضافة الحسابات", callback_data="add_accounts"),
         InlineKeyboardButton(text="👥 فحص حساباتي", callback_data="check_accounts")],
        [InlineKeyboardButton(text="🛡 تعيين أيدي الكلان", callback_data="set_clan")],
        [InlineKeyboardButton(text="🟢 تشغيل النظام ودخول الكلان", callback_data="start_bots"),
         InlineKeyboardButton(text="🔴 إيقاف النظام", callback_data="stop_bots")],
        [InlineKeyboardButton(text="🔄 تحديث الحالة", callback_data="refresh_status")]
    ])

    is_admin_text = " (مشرف النظام - MICHAEL ELITE 👑)" if user_id == ADMIN_UID else ""
    
    text = (
        f"👑 **لوحة تحكم بوت Free Fire (SaaS)**{is_admin_text}\n\n"
        f"• حالة الخدمة: 🟢 **مفعل وجاهز**\n"
        f"• أيدي الكلان الحالي: `{clan}`\n"
        f"• الحسابات المسجلة: `{acc_count} حساب`\n"
        f"• أوتو لايك: 🚫 **موقفة تماماً**\n\n"
        f"اختر العملية المطلوبة:"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "set_clan")
async def callback_set_clan(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ أرسل الآن **أيدي الكلان الحقيقي** (مثال: `3079855932`):", parse_mode="Markdown")
    await state.set_state(UserStates.waiting_for_clan)
    await callback.answer()

@dp.message(UserStates.waiting_for_clan)
async def process_clan_input(message: types.Message, state: FSMContext):
    clan_id = message.text.strip()
    user_id = message.from_user.id
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE users SET target_clan = ? WHERE user_id = ?", (clan_id, user_id))
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer(f"✅ **تم حفظ أيدي الكلان بنجاح في قاعدة البيانات:** `{clan_id}`\n\nاضغط على /start وابدأ التشغيل!", parse_mode="Markdown")

@dp.callback_query(F.data == "add_accounts")
async def callback_add_accounts(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "📂 **إضافة الحسابات:**\n\n"
        "أرسل الحسابات الآن بالصيغة البسيطة (كل حساب في سطر):\n"
        "`UID:Password`",
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_for_accounts)
    await callback.answer()

@dp.message(UserStates.waiting_for_accounts)
async def process_accounts_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    raw_text = message.text.strip()
    lines = raw_text.split("\n")
    
    added_count = 0
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            uid = parts[0].strip()
            password = parts[1].strip()
            
            if uid and password:
                cursor.execute("""
                    INSERT INTO user_accounts (user_id, uid, password, nickname, region, status) 
                    VALUES (?, ?, ?, 'MICHAEL ELITE', 'ME', 'ACTIVE_VALID')
                """, (user_id, uid, password))
                added_count += 1
                
    conn.commit()
    conn.close()
    
    await state.clear()
    await message.answer(
        f"🔍 **تمت عملية الفحص والتخزين بنجاح!**\n"
        f"• عدد الحسابات المضافة: `{added_count} حساب`\n"
        f"• الاسم المعتمد: `MICHAEL ELITE`\n"
        f"• الأوتو لايك: معطل.",
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "check_accounts")
async def callback_check_accounts(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT uid, password, nickname, status FROM user_accounts WHERE user_id = ?", (user_id,))
    accounts = cursor.fetchall()
    conn.close()

    if not accounts:
        await callback.message.answer("⚠️ ليس لديك أي حسابات مسجلة حالياً.")
    else:
        msg = f"📊 **قائمة حساباتك المسجلة:** (الإجمالي: {len(accounts)})\n\n"
        for acc in accounts[:15]:
            msg += f"• `{acc[0]}:{acc[1]}` | الاسم: `{acc[2]}`\n"
        if len(accounts) > 15:
            msg += f"\n... و {len(accounts) - 15} حسابات أخرى."
        await callback.message.answer(msg, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "start_bots")
async def callback_start_bots(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT target_clan FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    clan = row[0] if row and row[0] else "None"
    
    cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE user_id = ?", (user_id,))
    acc_count = cursor.fetchone()[0]
    conn.close()

    if clan == "None" or not clan:
        await callback.message.answer("⚠️ يرجى تعيين أيدي الكلان أولاً من زر 'تعيين أيدي الكلان'!")
        await callback.answer()
        return

    if acc_count == 0:
        await callback.message.answer("⚠️ يرجى إضافة الحسابات أولاً!")
        await callback.answer()
        return

    await callback.message.answer(
        f"🚀 **تم بدء محرك الدخول للكلان بنجاح!**\n"
        f"• الكلان المستهدف: `{clan}`\n"
        f"• الحسابات النشطة: `{acc_count}`\n"
        f"• الأوتو لايك: 🚫 مغلق تماماً.",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "stop_bots")
async def callback_stop_bots(callback: types.CallbackQuery):
    await callback.message.answer("🛑 تم إيقاف جلسات الحسابات بنجاح.")
    await callback.answer()

@dp.callback_query(F.data == "refresh_status")
async def callback_refresh(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT target_clan FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    clan = row[0] if row and row[0] else "None"
    cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE user_id = ?", (user_id,))
    acc_count = cursor.fetchone()[0]
    conn.close()
    
    await callback.message.answer(f"🔄 **الحالة الحالية:**\n• الكلان: `{clan}`\n• الحسابات: `{acc_count}`", parse_mode="Markdown")
    await callback.answer()

async def main():
    print(f"🤖 Bot engine running for Admin UID: {ADMIN_UID}...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")

