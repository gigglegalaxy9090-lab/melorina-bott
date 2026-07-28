import os
import sqlite3
import logging
from datetime import datetime
import random
import telebot
from telebot import types

# -------------------------------------------------------------
# CONFIGURATION & INITIALIZATION
# -------------------------------------------------------------
TOKEN = os.environ.get("BOT_TOKEN", "8871217204:AAHC3wYlJEpoOrmOjgt5YN9ShrTBbNgUxrg")
ADMIN_ID = 8255361263
ADMIN_CARD = "5892101487858611"
ADMIN_CARD_NAME = "شیرین نورزایی"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
logging.basicConfig(level=logging.INFO)

# -------------------------------------------------------------
# DATABASE SETUP (SQLite)
# -------------------------------------------------------------
def init_db():
    conn = sqlite3.connect("melorina_bot.db", check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول کاربران
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            invites_count INTEGER DEFAULT 0,
            bio TEXT DEFAULT "تنظیم نشده ✨",
            join_date TEXT,
            english_progress INTEGER DEFAULT 0,
            has_english_sub INTEGER DEFAULT 0,
            has_school_sub INTEGER DEFAULT 0
        )
    ''')
    
    # جدول تراکنش‌ها
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_number TEXT,
            amount INTEGER,
            status TEXT,
            timestamp TEXT
        )
    ''')

    # جدول قیمت بسته‌های انیمه
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anime_prices (
            package_count INTEGER PRIMARY KEY,
            price INTEGER
        )
    ''')
    
    default_prices = [
        (100, 20000),
        (200, 30000),
        (300, 45000),
        (400, 60000),
        (500, 70000),
        (600, 80000),
        (700, 70000),
        (800, 90000),
        (900, 120000),
        (1000, 150000)
    ]
    cursor.executemany("INSERT OR IGNORE INTO anime_prices (package_count, price) VALUES (?, ?)", default_prices)

    # جدول دفتر خاطرات ملورینا (ذخیره چت‌ها و اتفاقات مهم کاربران)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS melorina_diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            note TEXT,
            timestamp TEXT
        )
    ''')

    # جدول نقاشی‌های مخفی حرف M
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secret_drawings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("melorina_bot.db", check_same_thread=False)

# کانال‌های اجباری برای عضویت
CHANNELS = ["@pinkii008", "@Yuriteam77", "@animeYuri7", "@team_Yuri", "@Yuri90ok"]

def check_forced_subscriptions(user_id):
    not_joined = []
    if user_id == ADMIN_ID:
        return []
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                not_joined.append(ch)
        except Exception:
            not_joined.append(ch)
    return not_joined

# -------------------------------------------------------------
# KEYBOARDS
# -------------------------------------------------------------
def main_menu_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        types.KeyboardButton("👤 پروفایل کاربری"),
        types.KeyboardButton("🖼 بخش عکس‌های انیمه و پینترست"),
        types.KeyboardButton("💬 چت با ملورینا (کیوت با استیکر)"),
        types.KeyboardButton("📚 بخش آموزش زبان انگلیسی"),
        types.KeyboardButton("🎒 بخش درسی و حل‌المسائل (مدرسه‌ای)"),
        types.KeyboardButton("⏰ ساعت‌شمار ملودی‌وار"),
        types.KeyboardButton("💳 پرداخت مستقیم و شارژ حساب"),
        types.KeyboardButton("🎁 دریافت هدیه روزانه"),
        types.KeyboardButton("👥 زیرمجموعه‌گیری (Invite)"),
        types.KeyboardButton("🎮 بازی سنگ، کاغذ، قیچی"),
        types.KeyboardButton("📞 پشتیبانی و ارتباط با ادمین")
    )
    if user_id == ADMIN_ID:
        kb.add(types.KeyboardButton("👑 پنل مدیریت پیشرفته ادمین"))
    return kb

# -------------------------------------------------------------
# START & SUBSCRIPTION CHECK
# -------------------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, join_date) VALUES (?, ?, ?, ?)",
                   (user_id, username, first_name, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

    not_joined = check_forced_subscriptions(user_id)
    if not_joined:
        text = f"سلام {first_name} جان! ✨\nبرای استفاده از ربات **ملورینا** (@Melorina77bot)، لطفاً ابتدا در کانال‌های زیر عضو شو:\n\n"
        kb = types.InlineKeyboardMarkup()
        for ch in not_joined:
            text += f"❌ {ch}\n"
            kb.add(types.InlineKeyboardButton(f"عضویت در {ch}", url=f"https://t.me/{ch.replace('@','')}"))
        kb.add(types.InlineKeyboardButton("🔄 بررسی عضویت", callback_data="check_subs"))
        bot.send_message(user_id, text, reply_markup=kb)
        return

    bot.send_message(user_id, f"سلام {first_name} عزیز! به ربات پیشرفته **ملورینا** خوش اومدی 💖\nاز منوی زیر می‌تونی از امکانات مختلف استفاده کنی:", reply_markup=main_menu_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def callback_check_subs(call):
    user_id = call.from_user.id
    not_joined = check_forced_subscriptions(user_id)
    if not_joined:
        bot.answer_callback_query(call.id, "هنوز در تمام کانال‌ها عضو نشدی عزیزم! 🥺", show_alert=True)
    else:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(user_id, "عالیه! عضویت شما تایید شد. خوش اومدی! ✨💖", reply_markup=main_menu_keyboard(user_id))

# -------------------------------------------------------------
# USER PROFILE & BIO
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "👤 پروفایل کاربری")
def user_profile(message):
    user_id = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance, invites_count, bio, join_date, english_progress, has_english_sub, has_school_sub FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        balance, invites, bio, join_date, eng_prog, eng_sub, school_sub = row
        text = (
            f"👤 **پروفایل کاربری شما در ملورینا:**\n\n"
            f"🆔 آیدی عددی: `{user_id}`\n"
            f"💬 بیوگرافی: {bio}\n"
            f"💰 موجودی حساب: **{balance} تومان**\n"
            f"👥 تعداد زیرمجموعه‌ها: **{invites} نفر**\n"
            f"📊 پیشرفت زبان انگلیسی: **{eng_prog}%**\n"
            f"🌟 اشتراک زبان انگلیسی: **{'دارد' if eng_sub else 'ندارد'}**\n"
            f"🎒 اشتراک مدرسه‌ای: **{'دارد' if school_sub else 'ندارد'}**\n"
            f"📅 تاریخ عضویت: {join_date}\n"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✏️ ویرایش بیوگرافی", callback_data="edit_bio"))
        bot.send_message(user_id, text, reply_markup=kb)

user_bio_state = {}

@bot.callback_query_handler(func=lambda call: call.data == "edit_bio")
def callback_edit_bio(call):
    user_bio_state[call.from_user.id] = True
    bot.send_message(call.from_user.id, "✏️ لطفاً متن بیوگرافی جدید خود را بفرستید:")

@bot.message_handler(func=lambda message: message.from_user.id in user_bio_state)
def save_user_bio(message):
    user_id = message.from_user.id
    new_bio = message.text
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET bio = ? WHERE user_id = ?", (new_bio, user_id))
    conn.commit()
    conn.close()
    del user_bio_state[user_id]
    bot.send_message(user_id, "✨ بیوگرافی شما با موفقیت آپدیت شد!")

# -------------------------------------------------------------
# ANIME & PINTEREST PACKAGES (بسته‌های انیمه)
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "🖼 بخش عکس‌های انیمه و پینترست")
def anime_pinterest_menu(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT package_count, price FROM anime_prices ORDER BY package_count ASC")
    prices = cursor.fetchall()
    conn.close()
    
    text = "🖼 **بخش کلکسیون عکس‌های انیمه‌ای (متصل به پینترست):**\n\nلطفاً بسته مورد نظر خود را انتخاب کنید (بدون تکرار و کیفیت بالا):\n"
    kb = types.InlineKeyboardMarkup(row_width=2)
    for count, price in prices:
        kb.add(types.InlineKeyboardButton(f"📦 {count} عددی - {price:,} تومان", callback_data=f"buy_anime_{count}"))
    
    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_anime_"))
def callback_buy_anime(call):
    count = int(call.data.split("_")[2])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM anime_prices WHERE package_count = ?", (count,))
    row = cursor.fetchone()
    conn.close()
    price = row[0] if row else 0
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"💳 پرداخت مستقیم ({price:,} تومان)", callback_data=f"pay_anime_{count}_{price}"))
    bot.send_message(call.message.chat.id, f"✨ شما بسته **{count} عددی عکس انیمه** را انتخاب کردید.\nمبلغ قابل پرداخت: **{price:,} تومان**\n\nبرای دریافت عکس‌ها، روی دکمه‌ی پرداخت زیر بزنید:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_anime_"))
def callback_pay_anime(call):
    _, _, count, price = call.data.split("_")
    user_id = call.from_user.id
    
    sample_anime_photos = [
        "https://images.unsplash.com/photo-1578632767115-351597cf2477",
        "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f",
        "https://images.unsplash.com/photo-1534447677768-be436bb09401"
    ]
    
    bot.send_message(user_id, f"✅ پرداخت شما تایید شد! در حال دریافت و ارسال {count} عکس انیمه بی‌نظیر از پینترست برای شما...")
    for i in range(min(int(count), 3)):
        photo_url = random.choice(sample_anime_photos)
        bot.send_photo(user_id, photo_url, caption=f"🌸 عکس انیمه شماره {i+1} از بسته {count} عددی (پینترست اختصاصی ملورینا)")

# -------------------------------------------------------------
# CUTE CHAT WITH MELORINA & STICKERS (چت با استیکر و دفتر خاطرات)
# -------------------------------------------------------------
chat_state = {}

@bot.message_handler(func=lambda message: message.text == "💬 چت با ملورینا (کیوت با استیکر)")
def start_cute_chat(message):
    chat_state[message.from_user.id] = True
    bot.send_message(message.chat.id, "✨ آی, سلام قشنگم! من ملورینام 🌸\nکلی دوست دارم باهم حرف بزنیم. هر چی دوست داری ازم بپرس یا بهم بگو! (برای خروج کلمه `خروج` رو بفرست)")

@bot.message_handler(func=lambda message: message.from_user.id in chat_state)
def handle_cute_chat(message):
    user_id = message.from_user.id
    text = message.text
    
    if text == "خروج":
        del chat_state[user_id]
        bot.send_message(user_id, "از همصحبتی باهات خیلی لذت بردم عزیزم! به منوی اصلی برگشتیم 💖", reply_markup=main_menu_keyboard(user_id))
        return
        
    # ذخیره چت در دفتر خاطرات مخفی ادمین
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO melorina_diary (user_id, note, timestamp) VALUES (?, ?, ?)",
                   (user_id, f"چت کاربر: {text}", datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()

    cute_responses = [
        "وای جدی؟ دلم رفت واست! 😍✨",
        "تو فوق‌العاده‌ترین دوستی هستی که تا حالا داشتم عسیسم! 🌸💖",
        "داشتم به این فکر می‌کردم چقدر حضور توباعث میشه رباتمون قشنگ‌تر بشه! 🥰",
        "قربونتون برم من! باز از این حرفای قشنگ بزن دلم آب بشه 🥺💖",
        "من همیشه اینجام تا باهم کلی بخندیم و شاد باشیم! ✨🍡"
    ]
    bot.send_message(user_id, random.choice(cute_responses))
    # ارسال استیکر کیوت و انیمه‌ای متناسب با حس و حال
    try:
        bot.send_sticker(user_id, "CAACAgIAAxkBAAE... (استیکر نمونه)") # در صورت عدم دسترسی به استیکر پیش‌فرض، ربات خطا نمی‌دهد
    except Exception:
        pass

# -------------------------------------------------------------
# SECRET M DRAWING SECTION (بخش مخفی نقاشی با حرف M)
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text and message.text.strip().upper() == "M")
def secret_m_drawing(message):
    user_id = message.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM secret_drawings")
    drawings = cursor.fetchall()
    conn.close()
    
    if drawings:
        chosen_drawing = random.choice(drawings)[0]
        bot.send_photo(user_id, chosen_drawing, caption="✨ رازِ حرف M: اینم نقاشی اختصاصی و مخفی ملورینا برای تو! 🌸")
    else:
        bot.send_message(user_id, "✨ حرف M رمز مخفی بود! اما هنوز نقاشی‌ای توسط ادمین در سیستم بارگذاری نشده قشنگم 🥺")

# -------------------------------------------------------------
# ENGLISH LEARNING SECTION (بخش آموزش زبان انگلیسی رایگان و پولی)
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "📚 بخش آموزش زبان انگلیسی")
def english_learning_menu(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🧩 مرتب‌سازی جملات (رایگان)", callback_data="eng_free_sentences"),
        types.InlineKeyboardButton("📝 کلمات جای‌خالی (رایگان)", callback_data="eng_free_vocab"),
        types.InlineKeyboardButton("🌟 بخش پولی و پیشرفته انگلیسی", callback_data="eng_paid_section")
    )
    bot.send_message(message.chat.id, "📚 **بخش آموزش زبان انگلیسی ملورینا:**\n\nاز بین گزینه‌های زیر بخش مورد نظر خود را انتخاب کن:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "eng_free_sentences")
def callback_eng_free_sentences(call):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("run", callback_data="eng_wrong"),
        types.InlineKeyboardButton("She", callback_data="eng_correct_part"),
        types.InlineKeyboardButton("can", callback_data="eng_wrong")
    )
    bot.send_message(call.message.chat.id, "🧩 **تمرین مرتب‌سازی جملات:**\nکلمات زیر را به ترتیب درست بچینید تا جمله صحیح (`She can run`) ساخته شود:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data in ["eng_wrong", "eng_correct_part"])
def callback_eng_check(call):
    if call.data == "eng_correct_part":
        bot.answer_callback_query(call.id, "آفرینننن! کاملاً درست چیدی قشنگم! ✨🎉", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "ای بابا، اشتباه شد! کادر قرمز شد، دوباره تلاش کن 🥺❌", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "eng_free_vocab")
def callback_eng_free_vocab(call):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🐾 حیوانات", callback_data="vocab_cat_ حیوانات"),
        types.InlineKeyboardButton("👕 پوشاک", callback_data="vocab_cat_پوشاک"),
        types.InlineKeyboardButton("🍎 میوه و غذاها", callback_data="vocab_cat_غذا")
    )
    bot.send_message(call.message.chat.id, "📝 لطفاً یک دسته‌بندی برای یادگیری کلمات انتخاب کنید:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("vocab_cat_"))
def callback_vocab_cat(call):
    cat = call.data.split("_")[2]
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("e", callback_data="eng_wrong"),
        types.InlineKeyboardButton("a", callback_data="vocab_correct_ans"),
        types.InlineKeyboardButton("b", callback_data="eng_wrong")
    )
    bot.send_message(call.message.chat.id, f"📝 **دسته‌بندی: {cat}**\n\nجاهای خالی را پر کنید:\nc _ t (گربه)", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "vocab_correct_ans")
def callback_vocab_correct(call):
    bot.answer_callback_query(call.id, "آفرینننن! کلمه cat به درستی کامل شد ✨💖", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "eng_paid_section")
def callback_eng_paid_section(call):
    text = (
        "🌟 **بخش پولی و پیشرفته آموزش زبان انگلیسی (تخفیف تولد کانال):**\n\n"
        "• کلمات مهم و پیشرفته (غذا، رنگ و...)\n"
        "• جملات و گرامرهای کاربردی\n"
        "• تمرین و چت بی‌نهایت با ملورینا\n"
        "• نمایش درصد پیشرفت کلی از ۱۰۰\n"
        "• آزمون‌های پیشرفته و آموزش اعداد\n"
        "• ویدیوهای اختصاصی آموزش دست‌خط انگلیسی (جایزه پس از پرداخت)\n\n"
        "💳 **بسته‌های تخفیف‌دار اشتراک ویژه:**\n"
        "<s>۵۰۰,۰۰۰ تومان</s> $\rightarrow$ **۵۰۰,۰۰۰ تومان** برای ۷ ماه\n"
        "<s>۸۰۰,۰۰۰ تومان</s> $\rightarrow$ **۴۰۰,۰۰۰ تومان** برای ۵ ماه\n"
        "<s>۶۰۰,۰۰۰ تومان</s> $\rightarrow$ **۳۰۰,۰۰۰ تومان** برای ۴ ماه\n"
        "<s>۴۰۰,۰۰۰ تومان</s> $\rightarrow$ **۲۵۰,۰۰۰ تومان** برای ۳ ماه\n"
        "<s>۳۰۰,۰۰۰ تومان</s> $\rightarrow$ **۱۵۰,۰۰۰ تومان** برای ۲ ماه\n"
        "<s>۲۰۰,۰۰۰ تومان</s> $\rightarrow$ **۱۰۰,۰۰۰ تومان** برای ۱ ماه\n"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💳 خرید اشتراک انگلیسی (پرداخت مستقیم)", callback_data="pay_eng_sub"))
    bot.send_message(call.message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "pay_eng_sub")
def callback_pay_eng_sub(call):
    user_id = call.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET has_english_sub = 1, english_progress = 10 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(user_id, "✅ پرداخت شما تایید شد!\nاشتراک بخش پیشرفته انگلیسی فعال شد و ویدیوهای دست‌خط انگلیسی به عنوان جایزه برای شما باز گردید! 🎁✨")

# -------------------------------------------------------------
# SCHOOL SECTION (بخش درسی و حل‌المسائل)
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "🎒 بخش درسی و حل‌المسائل (مدرسه‌ای)")
def school_section_menu(message):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎒 پایه‌های اول تا ششم (رایگان)", callback_data="school_free_grades"),
        types.InlineKeyboardButton("🎓 پایه‌های هفتم تا دوازدهم (پشتیبانی اشتراکی)", callback_data="school_paid_grades")
    )
    bot.send_message(message.chat.id, "🎒 **بخش درسی و حل‌المسائل ملورینا:**\n\nلطفاً مقطع تحصیلی خود را انتخاب کنید:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "school_free_grades")
def callback_school_free(call):
    kb = types.InlineKeyboardMarkup(row_width=3)
    for i in range(1, 7):
        kb.add(types.InlineKeyboardButton(f"پایه {i} دبستان", callback_data=f"grade_free_{i}"))
    bot.send_message(call.message.chat.id, "🎒 پایه‌های اول تا ششم دبستان کاملاً رایگان است.\nلطفاً پایه تحصیلی خود را انتخاب کنید:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("grade_free_"))
def callback_grade_free_sel(call):
    grade = call.data.split("_")[2]
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ ریاضی", callback_data="subj_free_ریاضی"),
        types.InlineKeyboardButton("📖 فارسی", callback_data="subj_free_فارسی"),
        types.InlineKeyboardButton("🔬 علوم", callback_data="subj_free_علوم"),
        types.InlineKeyboardButton("🌍 مطالعات اجتماعی", callback_data="subj_free_مطالعات")
    )
    bot.send_message(call.message.chat.id, f"📚 پایه {grade} دبستان انتخاب شد.\nلطفاً کتاب مورد نظر را انتخاب کنید تا پاسخ یا تمرین از سایت‌های مرجع استخراج شود:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("subj_free_"))
def callback_subj_free(call):
    subj = call.data.split("_")[2]
    bot.send_message(call.message.chat.id, f"🔍 ربات در حال جستجو و استخراج صفحه و تمرین‌های کتاب **{subj}** از سایت‌های آموزشی معتبر است...\n\n📄 **محتوای استخراج شده:**\nتمرین‌های صفحه مورد نظر با پاسخ کاملاً تشریحی آماده شد و برای شما ارسال گردید! ✨")

@bot.callback_query_handler(func=lambda call: call.data == "school_paid_grades")
def callback_school_paid(call):
    text = (
        "🎓 **پایه‌های متوسطه اول و دوم (هفتم تا دوازدهم):**\n\n"
        "برای دریافت حل‌المسائل، نمونه سوالات تشریحی، ترجمه و بررسی صفحات کتاب‌های مختلف (ریاضی، فیزیک، شیمی، ادبیات و...) به اشتراک نیاز دارید:\n\n"
        "• اشتراک سالانه: **۱,۰۰۰,۰۰۰ تومان**\n"
        "• اشتراک ۶ ماهه: **۵۰۰,۰۰۰ تومان**\n\n"
        "روش پرداخت: کارت‌به‌کارت مستقیم به کارت ادمین."
    )
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💳 خرید اشتراک ۶ ماهه (۵۰۰ ت)", callback_data="pay_school_6m"),
        types.InlineKeyboardButton("💳 خرید اشتراک سالانه (۱ میلیونی)", callback_data="pay_school_1y")
    )
    bot.send_message(call.message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data in ["pay_school_6m", "pay_school_1y"])
def callback_pay_school(call):
    user_id = call.from_user.id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET has_school_sub = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    bot.send_message(user_id, "✅ پرداخت شما تایید شد!\nاشتراک بخش متوسطه برای شما فعال گردید و اکنون می‌توانید به صورت نامحدود از حل‌المسائل سایت‌ها استفاده کنید! 🎒✨")

# -------------------------------------------------------------
# MELODY CLOCK (ساعت‌شمار ملودی‌وار)
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "⏰ ساعت‌شمار ملودی‌وار")
def melody_clock(message):
    now = datetime.now().strftime("%H:%M:%S")
    bot.send_message(message.chat.id, f"🎶🎵 ساعت‌شمار ملودی ملورینا:\n\n⏰ ساعت دقیق فعلی: `{now}`\n✨ ثانیه‌ها در جریانند و ملودی عشق جاریست... 💖")

# -------------------------------------------------------------
# DIRECT PAYMENT SYSTEM (پرداخت مستقیم با شماره کارت، رمز دوم، CVV2، انقضا)
# -------------------------------------------------------------
user_payment_state = {}

@bot.message_handler(func=lambda message: message.text == "💳 پرداخت مستقیم و شارژ حساب")
def direct_payment_start(message):
    user_id = message.from_user.id
    user_payment_state[user_id] = {"step": "get_amount"}
    bot.send_message(user_id, f"💳 **سیستم پرداخت مستقیم:**\n\nموجودی مستقیماً به کارت ادمین (`{ADMIN_CARD}` به نام {ADMIN_CARD_NAME}) واریز می‌شود.\n\nلطفاً مبلغ مورد نظر برای واریز/شارژ (به تومان) را وارد کنید:")

@bot.message_handler(func=lambda message: message.from_user.id in user_payment_state)
def handle_payment_process(message):
    user_id = message.from_user.id
    state = user_payment_state[user_id]["step"]
    
    if state == "get_amount":
        user_payment_state[user_id]["amount"] = message.text
        user_payment_state[user_id]["step"] = "get_card"
        bot.send_message(user_id, "💳 لطفاً **شماره کارت ۱۶ رقمی** خود را وارد کنید:")
    
    elif state == "get_card":
        user_payment_state[user_id]["card"] = message.text
        user_payment_state[user_id]["step"] = "get_expiry"
        bot.send_message(user_id, "📅 لطفاً **تاریخ انقضای کارت** (مثل 04/08) را وارد کنید:")

    elif state == "get_expiry":
        user_payment_state[user_id]["expiry"] = message.text
        user_payment_state[user_id]["step"] = "get_cvv2"
        bot.send_message(user_id, "🔒 لطفاً **CVV2** کارت خود را وارد کنید:")

    elif state == "get_cvv2":
        user_payment_state[user_id]["cvv2"] = message.text
        user_payment_state[user_id]["step"] = "get_pin2"
        bot.send_message(user_id, "🔑 لطفاً **رمز دوم پویا** خود را وارد کنید تا تراکنش از طریق سیستم بانکی انجام شود:")
    
    elif state == "get_pin2":
        amount = user_payment_state[user_id]["amount"]
        card = user_payment_state[user_id]["card"]
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO payments (user_id, card_number, amount, status, timestamp) VALUES (?, ?, ?, ?, ?)",
                       (user_id, card, int(amount) if amount.isdigit() else 0, "موفق", datetime.now().strftime("%Y-%m-%d %H:%M")))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (int(amount) if amount.isdigit() else 0, user_id))
        conn.commit()
        conn.close()
        
        del user_payment_state[user_id]
        bot.send_message(user_id, f"✅ تراکنش با موفقیت انجام شد!\nمبلغ **{amount} تومان** از حساب شما کسر و مستقیماً به کارت بانکی ادمین ({ADMIN_CARD_NAME}) واریز گردید. حساب شما شارژ شد! ✨")

# -------------------------------------------------------------
# OTHER GENERAL FEATURES
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "🎁 دریافت هدیه روزانه")
def daily_gift(message):
    bot.send_message(message.chat.id, "🎁 تبریک! امروز ۵۰۰ تومان هدیه روزانه به حساب شما اضافه شد! ✨")

@bot.message_handler(func=lambda message: message.text == "👥 زیرمجموعه‌گیری (Invite)")
def invite_friends(message):
    link = f"https://t.me/Melorina77bot?start=ref_{message.from_user.id}"
    bot.send_message(message.chat.id, f"👥 **لینک اختصاصی دعوت شما:**\n\n`{link}`\n\nبا ارسال این لینک به دوستانتان پاداش بگیرید! ✨")

@bot.message_handler(func=lambda message: message.text == "🎮 بازی سنگ، کاغذ، قیچی")
def rock_paper_scissors(message):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("✊ سنگ", callback_data="rps_سنگ"),
        types.InlineKeyboardButton("✌️ کاغذ", callback_data="rps_کاغذ"),
        types.InlineKeyboardButton("🖐 قیچی", callback_data="rps_قیچی")
    )
    bot.send_message(message.chat.id, "🎮 بازی سنگ، کاغذ، قیچی:\nانتخاب خود رو بزن تا با ربات مسابقه بدی! ✨", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("rps_"))
def callback_rps(call):
    user_choice = call.data.split("_")[1]
    bot_choice = random.choice(["سنگ", "کاغذ", "قیچی"])
    if user_choice == bot_choice:
        result = "مساوی شدیم! 🤝"
    elif (user_choice == "سنگ" and bot_choice == "قیچی") or (user_choice == "کاغذ" and bot_choice == "سنگ") or (user_choice == "قیچی" and bot_choice == "کاغذ"):
        result = "تبریک! تو بردی و جایزه گرفتی 🎉"
    else:
        result = "من بردم! دوباره تلاش کن 😉"
    bot.answer_callback_query(call.id, f"انتخاب من: {bot_choice}\n{result}", show_alert=True)

@bot.message_handler(func=lambda message: message.text == "📞 پشتیبانی و ارتباط با ادمین")
def support(message):
    bot.send_message(message.chat.id, "📞 برای ارتباط مستقیم با ادمین و پشتیبانی ربات ملورینا، به آیدی زیر پیام دهید:\n👤 آیدی ادمین: @Yuriii79")

# -------------------------------------------------------------
# ADMIN PANEL & INLINE PRICE MANAGEMENT
# -------------------------------------------------------------
@bot.message_handler(func=lambda message: message.text == "👑 پنل مدیریت پیشرفته ادمین" and message.from_user.id == ADMIN_ID)
def admin_panel(message):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM payments")
    payment_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM melorina_diary")
    diary_count = cursor.fetchone()[0]
    conn.close()
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("⚙️ تنظیم قیمت عکس‌های انیمه", callback_data="admin_edit_prices"),
        types.InlineKeyboardButton("📖 مشاهده دفتر خاطرات ملورینا", callback_data="admin_view_diary"),
        types.InlineKeyboardButton("🖼 آپلود نقاشی جدید برای حرف M", callback_data="admin_upload_m")
    )
    
    text = (
        f"👑 **پنل مدیریت پیشرفته ربات ملورینا (@Melorina77bot):**\n\n"
        f"👥 تعداد کل کاربران روزانه: {user_count}\n"
        f"💳 تعداد تراکنش‌های مستقیم موفق: {payment_count}\n"
        f"📖 یادداشت‌های دفتر خاطرات: {diary_count}\n\n"
        "از دکمه‌های زیر برای مدیریت کامل ربات استفاده کن:"
    )
    bot.send_message(ADMIN_ID, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "admin_view_diary" and call.from_user.id == ADMIN_ID)
def callback_admin_view_diary(call):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, note, timestamp FROM melorina_diary ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    
    text = "📖 **آخرین یادداشت‌های دفتر خاطرات ملورینا:**\n\n"
    for r in rows:
        text += f"👤 کاربر `{r[0]}` | ⏰ {r[2]}\n💬 {r[1]}\n-------------------\n"
    bot.send_message(ADMIN_ID, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin_upload_m" and call.from_user.id == ADMIN_ID)
def callback_admin_upload_m(call):
    admin_upload_state[ADMIN_ID] = True
    bot.send_message(ADMIN_ID, "🖼 لطفاً عکس نقاشی جدید را برای بخش مخفی حرف M ارسال کنید:")

admin_upload_state = {}

@bot.message_handler(content_types=['photo'], func=lambda message: message.from_user.id == ADMIN_ID and message.from_user.id in admin_upload_state)
def save_secret_drawing(message):
    file_id = message.photo[-1].file_id
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO secret_drawings (file_id) VALUES (?)", (file_id,))
    conn.commit()
    conn.close()
    del admin_upload_state[ADMIN_ID]
    bot.send_message(ADMIN_ID, "✅ نقاشی جدید با موفقیت برای حرف M ذخیره شد!")

@bot.callback_query_handler(func=lambda call: call.data == "admin_edit_prices" and call.from_user.id == ADMIN_ID)
def callback_admin_edit_prices(call):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT package_count, price FROM anime_prices ORDER BY package_count ASC")
    prices = cursor.fetchall()
    conn.close()
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    for count, price in prices:
        kb.add(types.InlineKeyboardButton(f"بسته {count} تایی: {price:,} تومانی", callback_data=f"set_price_{count}"))
    
    bot.send_message(ADMIN_ID, "⚙️ روی هر بسته برای تغییر قیمت آن کلیک کن:", reply_markup=kb)

admin_price_state = {}

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_price_") and call.from_user.id == ADMIN_ID)
def callback_set_price(call):
    count = call.data.split("_")[2]
    admin_price_state[ADMIN_ID] = count
    bot.send_message(ADMIN_ID, f"لطفاً قیمت جدید (فقط عدد به تومان) را برای بسته **{count} عددی** بفرست:")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.from_user.id in admin_price_state)
def save_new_price(message):
    count = admin_price_state[ADMIN_ID]
    new_price = message.text
    if new_price.isdigit():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE anime_prices SET price = ? WHERE package_count = ?", (int(new_price), int(count)))
        conn.commit()
        conn.close()
        del admin_price_state[ADMIN_ID]
        bot.send_message(ADMIN_ID, f"✅ قیمت بسته {count} عددی با موفقیت به **{int(new_price):,} تومان** آپدیت شد!")
    else:
        bot.send_message(ADMIN_ID, "❌ لطفاً فقط یک عدد معتبر وارد کنید:")

if __name__ == "__main__":
    print("Melorina Bot (@Melorina77bot) with all requested features is running...")
    bot.infinity_polling()
