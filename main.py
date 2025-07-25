import os, json, time, random, hashlib, threading
import requests, schedule, telebot
from bs4 import BeautifulSoup
from telebot.types import ReactionTypeEmoji, InlineKeyboardMarkup, InlineKeyboardButton

# ========== تنظیمات اصلی ==========
BOT_TOKEN = "8449010749:AAG3NpJch9ArJES6WGLd3LUe71IVxK8vsU4"
ADMIN_ID = 1391667035
CHANNEL_ID = "@mamatestbotdoky"
DATA_FILE = "data.json"

# ========== دسته‌بندی‌ها و تنظیمات ==========
CATEGORIES = {
    "غمگین": {
        "url": "https://taw-bio.ir/category/Depressed",
        "reaction": "😔"
    },
    "موفقیت": {
        "url": "https://taw-bio.ir/category/Success",
        "reaction": "🏆"
    },
    "treason": {
        "url": "https://taw-bio.ir/category/treason",
        "reaction": "💔"
    },
    "عشق": {
        "url": "https://taw-bio.ir/category/Love",
        "reaction": "❤️"
    },
    "Horn": {
        "url": "https://taw-bio.ir/category/Horn",
        "reaction": "👑"
    }
}

CUSTOM_TEXTS = {
    "signature": "mamatestbotdoky",
    "no_permission": "⛔ فقط مدیر دسترسی دارد.",
    "fill_done": "✅ مطالب بروزرسانی شد!",
    "send_done": "✅ ارسال انجام شد!",
}

# ========== توابع مدیریت داده ==========
def init_data_file():
    return {
        "next_id": 1,
        "posts": [],
        "last_fill": 0,
        "last_sent": 0
    }

def load_data():
    if not os.path.exists(DATA_FILE):
        return init_data_file()
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return init_data_file()

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== توابع استخراج محتوا ==========
def extract_content(url, category):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        posts = []
        articles = soup.find_all('article', class_='iTxt')
        
        for article in articles:
            content_div = article.find('div', class_='t')
            if not content_div:
                continue
                
            content = content_div.get_text().strip()
            hashtags = [tag.get_text().strip() 
                       for tag in article.find_all('a', class_=['a_r', 'c', 'urlac', 'tg']) 
                       if tag.get_text().strip()]
            
            link_tag = article.find('a', class_='a_r')
            post_link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else url
            
            if not post_link.startswith('http'):
                post_link = f"https://taw-bio.ir{post_link}"
                
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            posts.append({
                'id': None,
                'content': content,
                'hashtags': hashtags,
                'url': post_link,
                'content_hash': content_hash,
                'category': category,
                'sent': False,
                'timestamp': time.time()
            })
            
        return posts
    except Exception as e:
        print(f"Error in extract_content: {str(e)}")
        return []

# ========== توابع فرمت و ارسال ==========
def format_post(post):
    hashtags = post.get('hashtags', [])[:2]
    tags = " ".join(f"#{tag}" for tag in hashtags) if hashtags else ""
    
    # فرمت جدید با نقل قول برای امضای کانال
    signature = f"\n\n——————————\n📌 @{CUSTOM_TEXTS['signature']}"
    return f"{post['content']}\n\n{tags}{signature}"

def send_post(post):
    try:
        text = format_post(post)
        sent_msg = bot.send_message(
            CHANNEL_ID, 
            text, 
            parse_mode="HTML",
            disable_web_page_preview=True
        )
        
        # افزودن ریاکشن مربوط به دسته‌بندی
        reaction_emoji = ReactionTypeEmoji(CATEGORIES[post['category']]['reaction'])
        bot.set_message_reaction(
            CHANNEL_ID, 
            sent_msg.message_id, 
            [reaction_emoji], 
            is_big=False
        )
        
        return True
    except Exception as e:
        print(f"Error in send_post: {str(e)}")
        return False

# ========== پنل مدیریت ==========
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, CUSTOM_TEXTS['no_permission'])
        return
        
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📊 وضعیت پست‌ها", callback_data="status"),
        InlineKeyboardButton("🔄 واکشی مطالب", callback_data="do_fill"),
        InlineKeyboardButton("📤 ارسال دستی", callback_data="send_manual")
    )
    bot.send_message(
        message.chat.id, 
        "🎛 پنل مدیریت ربات:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, CUSTOM_TEXTS['no_permission'])
        return
        
    data = load_data()
    
    if call.data == "status":
        total = len(data['posts'])
        unsent = sum(1 for p in data['posts'] if not p['sent'])
        
        # آمار دسته‌بندی‌ها
        categories = {cat: {"total": 0, "unsent": 0} for cat in CATEGORIES}
        for post in data['posts']:
            cat = post['category']
            categories[cat]["total"] += 1
            if not post['sent']:
                categories[cat]["unsent"] += 1
        
        # ساخت متن گزارش
        status_text = f"📊 آمار کلی:\n"
        status_text += f"• کل پست‌ها: {total}\n"
        status_text += f"• ارسال نشده: {unsent}\n\n"
        status_text += f"📋 آمار دسته‌بندی‌ها:\n"
        
        for cat, stats in categories.items():
            status_text += (
                f"• {cat}: {stats['total']} پست "
                f"({stats['unsent']} ارسال نشده)\n"
            )
        
        bot.edit_message_text(
            status_text,
            call.message.chat.id,
            call.message.message_id
        )
        
    elif call.data == "do_fill":
        bot.answer_callback_query(call.id, "در حال واکشی مطالب...")
        
        def fill_task():
            try:
                hashes = {p['content_hash'] for p in data['posts']}
                added_count = 0
                
                for cat, info in CATEGORIES.items():
                    posts = extract_content(info["url"], cat)
                    for post in posts:
                        if post['content_hash'] in hashes:
                            continue
                            
                        post['id'] = data['next_id']
                        data['next_id'] += 1
                        data['posts'].append(post)
                        added_count += 1
                        
                save_data(data)
                bot.send_message(call.message.chat.id, f"✅ {added_count} پست جدید افزوده شد")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"خطا در واکشی: {str(e)}")
        
        threading.Thread(target=fill_task).start()
        
    elif call.data == "send_manual":
        markup = InlineKeyboardMarkup(row_width=5)
        buttons = [
            InlineKeyboardButton(str(i), callback_data=f"manual_count_{i}") 
            for i in range(1, 11)
        ]
        markup.add(*buttons)
        markup.add(InlineKeyboardButton("🔙 بازگشت", callback_data="back_main"))
        
        bot.edit_message_text(
            "تعداد پست‌های ارسالی را انتخاب کنید:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup
        )
        
    elif call.data.startswith("manual_count_"):
        count = int(call.data.split("_")[-1])
        unsent = [p for p in data['posts'] if not p['sent']]
        
        if not unsent:
            bot.answer_callback_query(call.id, "⚠️ پست ارسال نشده‌ای وجود ندارد")
            return
        
        bot.answer_callback_query(call.id, f"در حال ارسال {count} پست...")
        
        def send_task():
            try:
                to_send = random.sample(unsent, min(count, len(unsent)))
                success_count = 0
                
                for post in to_send:
                    if send_post(post):
                        post['sent'] = True
                        success_count += 1
                    time.sleep(1)  # جلوگیری از محدودیت ارسال
                
                save_data(data)
                bot.send_message(call.message.chat.id, f"✅ {success_count} پست با موفقیت ارسال شد")
            except Exception as e:
                bot.send_message(call.message.chat.id, f"خطا در ارسال: {str(e)}")
        
        threading.Thread(target=send_task).start()
        
    elif call.data == "back_main":
        admin_panel(call.message)

# ========== اجرای زمان‌بندی‌ها ==========
def scheduler_thread():
    # زمان‌بندی‌ها:
    # هر 6 ساعت یکبار مطالب جدید واکشی شود
    schedule.every(6).hours.do(run_fill_command)
    
    # هر 3 ساعت یک پست ارسال شود
    schedule.every(3).hours.do(send_scheduled_posts)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

def run_fill_command():
    print("Starting fill process...")
    data = load_data()
    hashes = {p['content_hash'] for p in data['posts']}
    added_count = 0
    
    for cat, info in CATEGORIES.items():
        posts = extract_content(info["url"], cat)
        for post in posts:
            if post['content_hash'] in hashes:
                continue
                
            post['id'] = data['next_id']
            data['next_id'] += 1
            data['posts'].append(post)
            added_count += 1
            
    data['last_fill'] = time.time()
    save_data(data)
    print(f"Fill completed! Added {added_count} new posts.")

def send_scheduled_posts():
    data = load_data()
    unsent = [p for p in data['posts'] if not p['sent']]
    
    if not unsent:
        print("No unsent posts available.")
        return
        
    # انتخاب تصادفی از تمام دسته‌بندی‌ها
    post = random.choice(unsent)
    
    if send_post(post):
        post['sent'] = True
        data['last_sent'] = time.time()
        save_data(data)
        print(f"Sent post #{post['id']} from {post['category']} category")

# ========== اجرای اصلی ==========
if __name__ == "__main__":
    print("Starting bot and scheduler...")
    
    # اجرای زمان‌بندی‌ها در یک ریسه جداگانه
    scheduler_thread = threading.Thread(target=scheduler_thread, daemon=True)
    scheduler_thread.start()
    
    # اجرای بات
    bot.infinity_polling()