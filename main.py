import os
import requests
import re
from datetime import datetime

# --- تنظیمات ---
NODES_FILE = 'nodes.md'
README_FILE = 'README.md'
# این متغیرها از GitHub Secrets خوانده می‌شوند
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

def get_shadowsocks_servers(file_path):
    """از فایل ورودی، فقط لینک‌های شادوساکس (ss://) را استخراج می‌کند."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # با استفاده از regex فقط خطوطی که با ss:// شروع می‌شوند را پیدا می‌کنیم
        ss_links = re.findall(r'ss://[^\s]+', content)
        # حذف لینک‌های تکراری و مرتب‌سازی
        unique_links = sorted(list(set(ss_links)))
        print(f"تعداد {len(unique_links)} سرور شادوساکس پیدا شد.")
        return unique_links
    except FileNotFoundError:
        print(f"خطا: فایل {file_path} پیدا نشد.")
        return []

def update_readme(servers):
    """فایل README.md را با لیست سرورهای جدید آپدیت می‌کند."""
    if not servers:
        print("سروری برای آپدیت README پیدا نشد.")
        return

    # تاریخ و زمان فعلی برای نمایش در README
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    content = f"# Shadowsocks Servers\n\n"
    content += f"**Last Updated:** `{now}` (UTC)\n\n"
    content += "```\n"
    content += "\n".join(servers)
    content += "\n```\n"

    try:
        with open(README_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"فایل {README_FILE} با موفقیت آپدیت شد.")
    except Exception as e:
        print(f"خطا در نوشتن فایل README: {e}")


def send_to_telegram(servers):
    """لیست سرورها را به کانال تلگرام ارسال می‌کند."""
    if not servers or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("اطلاعات تلگرام ناقص است یا سروری برای ارسال وجود ندارد. از ارسال پیام صرف‌نظر شد.")
        return

    message_text = "🚀 **لیست جدید سرورهای Shadowsocks** 🚀\n\n"
    message_text += f"**تعداد:** `{len(servers)}` سرور\n"
    message_text += f"**تاریخ آپدیت:** `{datetime.now().strftime('%Y-%m-%d %H:%M')}`\n\n"
    
    # برای جلوگیری از طولانی شدن پیام، می‌توانیم فقط تعدادی را بفرستیم یا همه را در یک بلاک کد
    message_text += "```\n"
    message_text += "\n".join(servers)
    message_text += "\n```"
    
    # API تلگرام برای ارسال پیام
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # برای جلوگیری از خطای پیام طولانی تلگرام (حداکثر 4096 کاراکتر)
    if len(message_text) > 4096:
        print("پیام برای ارسال به تلگرام بیش از حد طولانی است. پیام خلاصه‌شده ارسال می‌شود.")
        message_text = (
            f"🚀 **آپدیت جدید سرورهای Shadowsocks**\n"
            f"**تعداد:** `{len(servers)}` سرور جدید پیدا شد.\n"
            f"برای مشاهده لیست کامل، به ریپازیتوری گیت‌هاب مراجعه کنید."
        )

    payload = {
        'chat_id': TELEGRAM_CHANNEL_ID,
        'text': message_text,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("پیام با موفقیت به تلگرام ارسال شد.")
        else:
            print(f"خطا در ارسال پیام به تلگرام: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"خطا در ارتباط با سرور تلگرام: {e}")


if __name__ == "__main__":
    ss_servers = get_shadowsocks_servers(NODES_FILE)
    if ss_servers:
        update_readme(ss_servers)
        send_to_telegram(ss_servers)
    else:
        print("هیچ سرور شادوساکسی پیدا نشد. عملیات متوقف شد.")
