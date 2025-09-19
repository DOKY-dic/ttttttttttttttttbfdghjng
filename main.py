import asyncio
import logging
import sys
import subprocess
import importlib
import csv
import json
from datetime import datetime
from telethon import TelegramClient, errors
from telethon.tl.types import User, Channel
import colorama
from colorama import Fore, Style

# Initialize colorama
colorama.init()

# تنظیمات پیشرفته لاگ
class CustomFormatter(logging.Formatter):
    """فرمت‌دهنده رنگی برای لاگ‌ها"""
    format = "%(asctime)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.INFO: Fore.GREEN + format + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + format + Style.RESET_ALL,
        logging.ERROR: Fore.RED + format + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + format + Style.RESET_ALL,
        logging.DEBUG: Fore.BLUE + format + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# تنظیمات لاگ
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler برای console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)

# Handler برای فایل
fh = logging.FileHandler(f'coffee_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
fh.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(file_formatter)
logger.addHandler(fh)

def install_required_packages():
    """نصب خودکار پکیج‌های مورد نیاز"""
    required_packages = {
        'telethon': 'telethon',
        'colorama': 'colorama'
    }
    
    for package_name, install_name in required_packages.items():
        try:
            importlib.import_module(package_name)
            logger.info(f"✅ {package_name} از قبل نصب است")
        except ImportError:
            logger.info(f"📦 در حال نصب {package_name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", install_name])
                logger.info(f"✅ {package_name} با موفقیت نصب شد")
            except subprocess.CalledProcessError:
                logger.error(f"❌ خطا در نصب {package_name}")
                return False
    return True

class CoffeePromotionBot:
    def __init__(self):
        self.client = None
        self.stats = {
            'total_members': 0,
            'messages_sent': 0,
            'messages_failed': 0,
            'start_time': None,
            'end_time': None
        }
        self.message_log = []
        self.member_data = []
    
    def create_coffee_message(self):
        """ایجاد پیام تبلیغاتی حرفه‌ای برای قهوه"""
        message = """☕️ **پخش اختصاصی قهوه در استان قم** ☕️

🌟 **ویژگی‌های منحصر به فرد قهوه ما:**
• ✅ قهوه اصل و با کیفیت عالی
• ✅ آسیاب تازه و روزانه
• ✅ ترکیبات ویژه و طعم‌های منحصر به فرد
• ✅ مناسب برای تمام سلیقه‌ها

🏪 **خدمات ما:**
• 🔥 قهوه ترک و اسپرسو
• 🍵 انواع کاپوچینو و لاته
• 🎁 بسته‌بندی شکیل و هدیه
• 🚚 ارسال رایگان در شهر قم

📞 **برای سفارش و اطلاعات بیشتر:**
• 📲 تماس: 0912-XXX-XXXX
• 📍 آدرس: قم، میدان معلم، پخش قهوه اختصاصی

⏰ **ساعات کاری:** 
• روزهای شنبه تا پنجشنبه: ۸ صبح تا ۱۰ شب
• جمعه‌ها: ۴ بعدازظهر تا ۱۰ شب

✨ **اولین سفارش: ۲۰٪ تخفیف ویژه!**
کد تخفیف: **COFFEE20**

☕️ *یک فنجان قهوه فوق‌العاده رو از دست نده!*"""
        
        return message
    
    async def initialize_client(self, api_id, api_hash, phone_number):
        """راه‌اندازی کلاینت تلگرام"""
        try:
            self.client = TelegramClient(
                session=f'session_{phone_number}',
                api_id=api_id,
                api_hash=api_hash,
                device_model="Coffee Promotion Bot",
                system_version="1.0",
                app_version="2.0"
            )
            
            await self.client.start(phone=phone_number)
            logger.info("✅ کلاینت تلگرام راه‌اندازی شد")
            return True
            
        except errors.PhoneNumberInvalidError:
            logger.error("❌ شماره تلفن نامعتبر است")
        except errors.PhoneCodeInvalidError:
            logger.error("❌ کد تأیید نامعتبر است")
        except errors.PhoneCodeExpiredError:
            logger.error("❌ کد تأیید منقضی شده است")
        except errors.SessionPasswordNeededError:
            logger.error("❌ نیاز به رمز دوم (2FA) است")
        except Exception as e:
            logger.error(f"❌ خطا در راه‌اندازی کلاینت: {e}")
        
        return False
    
    async def get_group_info(self, group_link):
        """دریافت اطلاعات گروه و استخراج اعضا"""
        try:
            entity = await self.client.get_entity(group_link)
            
            if isinstance(entity, Channel):
                participants = await self.client.get_participants(entity)
                real_users = [p for p in participants if isinstance(p, User) and not p.bot]
                
                # ذخیره اطلاعات اعضا
                self.member_data = []
                for user in real_users:
                    self.member_data.append({
                        'user_id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'phone': user.phone,
                        'is_bot': user.bot
                    })
                
                group_info = {
                    'entity': entity,
                    'title': entity.title,
                    'id': entity.id,
                    'member_count': len(real_users),
                    'participants': real_users
                }
                
                logger.info(f"✅ گروه پیدا شد: {entity.title}")
                logger.info(f"👥 تعداد اعضای واقعی: {len(real_users)}")
                
                return group_info
            else:
                logger.error("❌ لینک مربوط به گروه نیست")
                return None
                
        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاعات گروه: {e}")
            return None
    
    async def send_message_to_members(self, group_info, message_text, delay_between_messages=3, max_messages=30):
        """ارسال پیام به اعضای گروه"""
        if not group_info or not group_info['participants']:
            logger.error("❌ اطلاعات گروه یا لیست اعضا نامعتبر است")
            return False
        
        self.stats['start_time'] = datetime.now()
        self.stats['total_members'] = len(group_info['participants'])
        
        logger.info(f"📨 شروع ارسال پیام به {len(group_info['participants'])} عضو...")
        
        success_count = 0
        fail_count = 0
        
        for i, user in enumerate(group_info['participants'][:max_messages]):
            try:
                # ارسال پیام
                await self.client.send_message(user.id, message_text)
                success_count += 1
                self.stats['messages_sent'] += 1
                
                # لاگ پیام موفق
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user.id,
                    'username': user.username or 'ندارد',
                    'first_name': user.first_name or 'ندارد',
                    'status': 'success',
                    'message': 'پیام تبلیغاتی قهوه'
                }
                self.message_log.append(log_entry)
                
                logger.info(f"✅ [{i+1}/{min(len(group_info['participants']), max_messages)}] "
                           f"پیام به {user.first_name or 'کاربر'} ارسال شد")
                
                # تأخیر بین پیام‌ها
                if i < len(group_info['participants'][:max_messages]) - 1:
                    await asyncio.sleep(delay_between_messages)
                    
            except errors.FloodWaitError as e:
                fail_count += 1
                self.stats['messages_failed'] += 1
                logger.warning(f"⏳ FloodWait: منتظر {e.seconds} ثانیه...")
                await asyncio.sleep(e.seconds)
                
            except Exception as e:
                fail_count += 1
                self.stats['messages_failed'] += 1
                logger.error(f"❌ خطا در ارسال به {user.first_name or 'کاربر'}: {e}")
                await asyncio.sleep(1)
        
        self.stats['end_time'] = datetime.now()
        return True
    
    async def send_report_to_admin(self, admin_username="@alireza_y85"):
        """ارسال گزارش به ادمین"""
        try:
            report_message = f"""📊 **گزارش اجرای ربات تبلیغاتی قهوه**

🏪 **موضوع:** پخش اختصاصی قهوه در قم
⏰ **زمان اجرا:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 **آمار ارسال:**
• ✅ پیام‌های موفق: {self.stats['messages_sent']}
• ❌ پیام‌های ناموفق: {self.stats['messages_failed']}
• 👥 کل اعضای گروه: {self.stats['total_members']}

🕒 **مدت زمان:** {self.stats['end_time'] - self.stats['start_time'] if self.stats['end_time'] else 'N/A'}

📋 **لیست اعضای گروه:** (تعداد: {len(self.member_data)})
"""
            # ارسال گزارش به ادمین
            await self.client.send_message(admin_username, report_message)
            logger.info(f"✅ گزارش به {admin_username} ارسال شد")
            
            # ارسال فایل لیست اعضا
            if self.member_data:
                csv_content = "User ID,Username,First Name,Last Name,Phone\n"
                for member in self.member_data:
                    csv_content += f"{member['user_id']},{member['username'] or 'N/A'},{member['first_name'] or 'N/A'},{member['last_name'] or 'N/A'},{member['phone'] or 'N/A'}\n"
                
                # ذخیره موقت و ارسال فایل
                with open('members_list.csv', 'w', encoding='utf-8') as f:
                    f.write(csv_content)
                
                await self.client.send_file(admin_username, 'members_list.csv', caption="📋 لیست کامل اعضای گروه")
                logger.info("✅ فایل لیست اعضا ارسال شد")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در ارسال گزارش: {e}")
            return False
    
    def save_logs(self):
        """ذخیره لاگ‌ها در فایل‌های مختلف"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # فایل CSV لاگ‌ها
            csv_filename = f'coffee_bot_log_{timestamp}.csv'
            with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'User ID', 'Username', 'First Name', 'Status'])
                
                for log in self.message_log:
                    writer.writerow([
                        log['timestamp'],
                        log.get('user_id', ''),
                        log.get('username', ''),
                        log.get('first_name', ''),
                        log.get('status', '')
                    ])
            
            # فایل CSV اعضا
            members_filename = f'group_members_{timestamp}.csv'
            with open(members_filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['User ID', 'Username', 'First Name', 'Last Name', 'Phone', 'Is Bot'])
                
                for member in self.member_data:
                    writer.writerow([
                        member['user_id'],
                        member['username'] or 'ندارد',
                        member['first_name'] or 'ندارد',
                        member['last_name'] or 'ندارد',
                        member['phone'] or 'ندارد',
                        'بله' if member['is_bot'] else 'خیر'
                    ])
            
            logger.info(f"💾 گزارش‌ها ذخیره شدند:")
            logger.info(f"   📄 {csv_filename} (لاگ ارسال)")
            logger.info(f"   👥 {members_filename} (لیست اعضا)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در ذخیره لاگ‌ها: {e}")
            return False
    
    def print_summary(self):
        """چاپ خلاصه گزارش در کنسول"""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            
            print("\n" + "=" * 60)
            print("🎯 خلاصه گزارش ربات تبلیغاتی قهوه")
            print("=" * 60)
            print(f"🏁 زمان شروع: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🛑 زمان پایان: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  مدت زمان: {duration}")
            print(f"👥 کل اعضای گروه: {self.stats['total_members']}")
            print(f"✅ پیام‌های موفق: {Fore.GREEN}{self.stats['messages_sent']}{Style.RESET_ALL}")
            print(f"❌ پیام‌های ناموفق: {Fore.RED}{self.stats['messages_failed']}{Style.RESET_ALL}")
            print(f"📋 اطلاعات {len(self.member_data)} عضو ذخیره شد")
            print("=" * 60)

async def main():
    """تابع اصلی"""
    print(Fore.CYAN + "=" * 60)
    print("🤖 ربات حرفه‌ای تبلیغات قهوه - قم")
    print("=" * 60 + Style.RESET_ALL)
    
    # نصب خودکار پکیج‌ها
    if not install_required_packages():
        return
    
    # اطلاعات API
    API_ID = 29302960
    API_HASH = 'a4d12409d7f982dc02842538a9c633a0'
    PHONE_NUMBER = '09208085485'
    GROUP_LINK = 'https://t.me/testmybot12j'
    ADMIN_USERNAME = "@alireza_y85"
    
    # ایجاد نمونه ربات
    bot = CoffeePromotionBot()
    
    try:
        # راه‌اندازی کلاینت
        if not await bot.initialize_client(API_ID, API_HASH, PHONE_NUMBER):
            return
        
        # دریافت اطلاعات گروه
        group_info = await bot.get_group_info(GROUP_LINK)
        if not group_info:
            return
        
        # ایجاد پیام تبلیغاتی
        message_text = bot.create_coffee_message()
        
        # نمایش پیام برای تأیید
        print(Fore.YELLOW + "\n📝 پیام تبلیغاتی:" + Style.RESET_ALL)
        print("=" * 50)
        print(message_text[:200] + "...")  # نمایش بخشی از پیام
        print("=" * 50)
        
        print(f"\n📋 گروه: {group_info['title']}")
        print(f"👥 تعداد اعضا: {group_info['member_count']}")
        
        confirm = input(Fore.RED + "\n⚠️  آیا می‌خواهید ارسال پیام شروع شود؟ (y/n): " + Style.RESET_ALL)
        if confirm.lower() != 'y':
            print("❌ ارسال لغو شد")
            return
        
        # ارسال پیام‌ها
        if await bot.send_message_to_members(
            group_info=group_info,
            message_text=message_text,
            delay_between_messages=3,  # تأخیر 3 ثانیه بین پیام‌ها
            max_messages=30  # حداکثر 30 پیام
        ):
            # ارسال گزارش به ادمین
            await bot.send_report_to_admin(ADMIN_USERNAME)
            
            # ذخیره لاگ‌ها
            bot.save_logs()
            
            # نمایش خلاصه
            bot.print_summary()
            
            print(Fore.GREEN + "🎉 ربات با موفقیت اجرا شد! گزارش به ادمین ارسال گردید." + Style.RESET_ALL)
        
    except KeyboardInterrupt:
        logger.warning("⏹️  ربات توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"❌ خطای غیرمنتظره: {e}")
    finally:
        if bot.client:
            await bot.client.disconnect()
            logger.info("🔌 اتصال قطع شد")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  برنامه توسط کاربر متوقف شد")
    except Exception as e:
        print(f"❌ خطای критиی: {e}")
    
    input("\nبرای خروج، Enter را فشار دهید...")
