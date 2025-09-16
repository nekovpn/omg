import requests
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
import time

# لیست لینک‌های منابع که حاوی کانفیگ‌های مختلف (از جمله شدوساکس) هستند
V2RAY_LINKS = [
    "https://raw.githubusercontent.com/MrPooyaX/VpnsFucking/main/BeVpn.txt",
    "https://raw.githubusercontent.com/yebekhe/TVC/main/subscriptions/xray/base64/mix",
    "https://raw.githubusercontent.com/ALIILAPRO/v2rayNG-Config/main/sub.txt",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/reality",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vless",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/vmess",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/trojan",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/protocols/shadowsocks",
    "https://raw.githubusercontent.com/ts-sf/fly/main/v2",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://mrpooya.top/SuperApi/BE.php",
]

def fetch_url(url):
    """محتوای یک URL را با تایم‌اوت مشخص دریافت می‌کند."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()  # در صورت وجود خطا، استثنا ایجاد می‌کند
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"خطا در دریافت اطلاعات از {url}: {e}")
        return None

def get_metadata_headers():
    """هدرهای متا دیتا برای فایل اشتراک (subscription) را برمی‌گرداند."""
    return """#profile-title: base64:8J+GkyBHaXQ6IEBGaXJtZm94IOKbk++4j+KAjfCfkqU=
#profile-update-interval: 1
#subscription-userinfo: upload=29; download=12; total=10737418240000000; expire=2546249531
#support-url: https://github.com/firmfox/Proxify
#profile-web-page-url: https://github.com/firmfox/Proxify\n"""

def generate_shadowsocks_file():
    """
    لینک‌های اشتراک را دریافت کرده، کانفیگ‌های شدوساکس را فیلتر می‌کند
    و آن‌ها را در فایل shadowsocks.txt ذخیره می‌کند.
    """
    shadowsocks_configs = set()
    
    print("در حال دریافت اطلاعات از لینک‌های اشتراک...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        # ارسال تمام URLها به executor برای اجرای موازی
        future_to_url = {executor.submit(fetch_url, url): url for url in V2RAY_LINKS}
        
        for future in future_to_url:
            data = future.result()
            if not data:
                continue

            # پردازش اطلاعات دریافت شده
            lines = []
            try:
                # تلاش برای دیکود کردن از Base64
                decoded_data = b64decode(data).decode('utf-8')
                lines = decoded_data.splitlines()
            except Exception:
                # اگر دیکود با خطا مواجه شد، آن را به عنوان متن ساده در نظر می‌گیریم
                lines = data.splitlines()

            # فیلتر کردن کانفیگ‌های شدوساکس
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.lower().startswith('ss://'):
                    shadowsocks_configs.add(stripped_line)

    if not shadowsocks_configs:
        print("هیچ کانفیگ شدوساکسی پیدا نشد.")
        return

    # ذخیره کانفیگ‌های جمع‌آوری شده در فایل
    print(f"تعداد {len(shadowsocks_configs)} کانفیگ یکتای شدوساکس پیدا شد. در حال ذخیره‌سازی در shadowsocks.txt...")
    with open('shadowsocks.txt', 'w', encoding='utf-8') as f:
        f.write(get_metadata_headers())
        # مرتب‌سازی کانفیگ‌ها برای خروجی یکسان
        sorted_configs = sorted(list(shadowsocks_configs))
        f.write('\n'.join(sorted_configs) + '\n')
    print("فایل shadowsocks.txt با موفقیت ایجاد شد.")

def main():
    """نقطه شروع اصلی برنامه."""
    start_time = time.time()
    
    generate_shadowsocks_file()
    
    end_time = time.time()
    print(f"\nعملیات در {end_time - start_time:.2f} ثانیه به پایان رسید.")

if __name__ == "__main__":
    main()
