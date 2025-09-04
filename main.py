import os
import re
import base64
import requests
import logging
from datetime import datetime
from urllib.parse import urlparse, unquote, urlunparse

# --- تنظیمات ---
NODES_FILE = 'nodes.md'
README_FILE = 'README.md'
NEW_TAG = 'proxyfig' # تگ جدید برای سرورها
REQUEST_TIMEOUT = 5 # 5 ثانیه برای هر درخواست

# این متغیرها از GitHub Secrets خوانده می‌شوند
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

# تنظیمات لاگ‌نویسی برای دیدن مراحل در GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_proxies_from_url(url):
    """محتوای یک URL را دانلود کرده، دیکود می‌کند و لیست پروکسی‌ها را برمی‌گرداند."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            logging.warning(f"Failed to fetch {url}. Status code: {response.status_code}")
            return []
        
        content = response.text
        # بعضی منابع لینک‌ها را مستقیم و برخی با base64 می‌دهند
        try:
            # تلاش برای دیکود base64
            decoded_content = base64.b64decode(content).decode('utf-8')
            proxies = decoded_content.splitlines()
        except (base64.binascii.Error, UnicodeDecodeError):
            # اگر base64 نبود، محتوای خام را در نظر بگیر
            proxies = content.splitlines()
            
        # تمیز کردن لیست و حذف خطوط خالی
        valid_proxies = [p.strip() for p in proxies if p.strip().startswith(('ss://', 'vmess://', 'vless://', 'trojan://', 'ssr://'))]
        logging.info(f"Found {len(valid_proxies)} proxies from {url}")
        return valid_proxies
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {url}: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {url}: {e}")
        return []

def change_shadowsocks_tag(ss_link, new_tag):
    """تگ (نام) یک لینک شادوساکس را تغییر می‌دهد."""
    try:
        # ساختار لینک ss: ss://method:password@server:port#tag
        parts = ss_link.split('#', 1)
        base_link = parts[0]
        # URL-encode the new tag to handle special characters
        encoded_tag = requests.utils.quote(new_tag)
        return f"{base_link}#{encoded_tag}"
    except Exception:
        # اگر لینک فرمت نامعتبر داشت، همان را برگردان
        return ss_link

def update_readme(servers):
    """فایل README.md را با لیست سرورهای شادوساکس آپدیت می‌کند."""
    if not servers:
        logging.info("No servers to update in README.")
        return

    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    content = (
        f"# Shadowsocks Servers\n\n"
        f"**Tag:** `{NEW_TAG}`\n"
        f"**Total Servers:** `{len(servers)}`\n"
        f"**Last Updated (UTC):** `{now_utc}`\n\n"
        f"**Subscription Link:**\n"
        f"```\n"
        f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY', '')}/main/ss_sub\n"
        f"```\n\n"
        f"**Server List:**\n"
        f"```\n"
        f"{'\n'.join(servers)}\n"
        f"```\n"
    )

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Successfully updated {README_FILE}")

def send_to_telegram(servers):
    """خلاصه نتایج را به کانال تلگرام ارسال می‌کند."""
    if not servers or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        logging.warning("Telegram credentials missing or no servers to send. Skipping notification.")
        return

    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    message_text = (
        f"🚀 **Shadowsocks Servers Update** 🚀\n\n"
        f"✅ `{len(servers)}` new servers found!\n"
        f"🏷️ **Tag:** `{NEW_TAG}`\n"
        f"⏰ **Updated (UTC):** `{now_utc}`\n\n"
        f"See the full list on GitHub:\n"
        f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHANNEL_ID, 'text': message_text, 'parse_mode': 'Markdown'}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logging.info("Successfully sent notification to Telegram.")
        else:
            logging.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"Error connecting to Telegram API: {e}")
        
def main():
    """تابع اصلی برنامه"""
    try:
        with open(NODES_FILE, 'r', encoding="utf8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"Fatal: {NODES_FILE} not found. Aborting.")
        return

    output_nodes_md = []
    all_found_proxies = set() # استفاده از set برای جلوگیری از پروکسی‌های تکراری

    # الگوی Regex برای پیدا کردن خطوط جدول
    table_line_pattern = re.compile(r'^\s*\|.*\|.*\|.*\|(https?://.*)\|')

    for line in lines:
        match = table_line_pattern.match(line)
        if match:
            url = match.group(1).strip()
            proxies = get_proxies_from_url(url)
            if proxies:
                all_found_proxies.update(proxies)
                status_icon = "✅"
                count = len(proxies)
            else:
                status_icon = "❌"
                count = 0
            
            # آپدیت خط مربوطه در nodes.md
            updated_line = re.sub(r'\|.*\|.*\|', f'| {status_icon} | {count} |', line, count=1)
            output_nodes_md.append(updated_line)
        else:
            # خطوطی که جزو جدول نیستند را دست‌نخورده اضافه کن
            output_nodes_md.append(line)

    # آپدیت فایل nodes.md با وضعیت جدید
    with open(NODES_FILE, "w", encoding="utf8") as f:
        f.write(''.join(output_nodes_md))
    logging.info(f"{NODES_FILE} has been updated with the latest statuses.")
    
    # فیلتر کردن فقط سرورهای شادوساکس و تغییر تگ آنها
    ss_servers_final = sorted([
        change_shadowsocks_tag(p, NEW_TAG)
        for p in all_found_proxies if p.startswith("ss://")
    ])
    
    logging.info(f"Total unique Shadowsocks servers found: {len(ss_servers_final)}")

    if ss_servers_final:
        # ساخت فایل اشتراک (subscription file)
        sub_content = '\n'.join(ss_servers_final)
        encoded_sub = base64.b64encode(sub_content.encode('utf-8')).decode('utf-8')
        with open('ss_sub', 'w', encoding='utf-8') as f:
            f.write(encoded_sub)
        logging.info("`ss_sub` subscription file created.")

        update_readme(ss_servers_final)
        send_to_telegram(ss_servers_final)
    else:
        logging.warning("No Shadowsocks servers found after processing all sources.")

if __name__ == "__main__":
    main()
