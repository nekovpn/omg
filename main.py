import os
import re
import base64
import requests
import logging
from datetime import datetime
from urllib.parse import quote

# --- Settings ---
NODES_FILE = 'nodes.md'
README_FILE = 'README.md'
SS_TEXT_FILE = 'ss.txt'  # <-- فایل جدید
SS_SUB_FILE = 'ss_sub'    # <-- فایل اشتراک
NEW_TAG = 'proxyfig'
REQUEST_TIMEOUT = 5

# These variables are read from GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

# Configure logging to see the steps in GitHub Actions
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_proxies_from_url(url):
    """Downloads content from a URL, decodes it, and returns a list of proxies."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            logging.warning(f"Failed to fetch {url}. Status code: {response.status_code}")
            return []
        
        content = response.text
        try:
            decoded_content = base64.b64decode(content).decode('utf-8')
            proxies = decoded_content.splitlines()
        except (base64.binascii.Error, UnicodeDecodeError):
            proxies = content.splitlines()
            
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
    """Changes the tag (name) of a Shadowsocks link."""
    try:
        parts = ss_link.split('#', 1)
        base_link = parts[0]
        encoded_tag = quote(new_tag)
        return f"{base_link}#{encoded_tag}"
    except Exception:
        return ss_link

def update_readme(servers):
    """Updates the README.md file with the list of Shadowsocks servers."""
    if not servers:
        logging.info("No servers to update in README.")
        return

    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    server_list_str = "\n".join(servers)
    
    repo_url = f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY', '')}/main"
    
    content = (
        f"# Shadowsocks Servers\n\n"
        f"**Tag:** `{NEW_TAG}`\n"
        f"**Total Servers:** `{len(servers)}`\n"
        f"**Last Updated (UTC):** `{now_utc}`\n\n"
        f"**Subscription Link (Base64):**\n"
        f"```\n{repo_url}/{SS_SUB_FILE}\n```\n\n"
        f"**Plain Text Link (for custom scripts):**\n"
        f"```\n{repo_url}/{SS_TEXT_FILE}\n```\n\n"
        f"**Server List:**\n"
        f"```\n{server_list_str}\n```\n"
    )

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Successfully updated {README_FILE}")

def send_to_telegram(servers):
    """Sends the list of servers to the Telegram channel, splitting into multiple messages if necessary."""
    if not servers or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        logging.warning("Telegram credentials missing or no servers to send. Skipping notification.")
        return

    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    header = (
        f"🚀 **Shadowsocks Servers Update** 🚀\n\n"
        f"✅ `{len(servers)}` servers found!\n"
        f"🏷️ **Tag:** `{NEW_TAG}`\n"
        f"⏰ **Updated (UTC):** `{now_utc}`\n"
    )

    full_server_list = "\n".join(servers)
    char_limit = 4000

    if len(header) + len(full_server_list) + 10 < char_limit:
        message_text = f"{header}\n```\n{full_server_list}\n```"
        messages_to_send = [message_text]
    else:
        messages_to_send = [header]
        current_chunk = ""
        for server in servers:
            if len(current_chunk) + len(server) + 1 > char_limit - 10:
                messages_to_send.append(f"```\n{current_chunk.strip()}\n```")
                current_chunk = ""
            current_chunk += server + "\n"
        
        if current_chunk:
            messages_to_send.append(f"```\n{current_chunk.strip()}\n```")

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    for i, message in enumerate(messages_to_send):
        payload = {'chat_id': TELEGRAM_CHANNEL_ID, 'text': message, 'parse_mode': 'Markdown', 'disable_web_page_preview': True}
        try:
            response = requests.post(api_url, json=payload, timeout=15)
            if response.status_code == 200:
                logging.info(f"Successfully sent message part {i+1}/{len(messages_to_send)} to Telegram.")
            else:
                logging.error(f"Failed to send Telegram message part {i+1}: {response.status_code} - {response.text}")
                break
        except Exception as e:
            logging.error(f"Error connecting to Telegram API for message part {i+1}: {e}")
            break

def main():
    """The main function of the script."""
    try:
        with open(NODES_FILE, 'r', encoding="utf8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"Fatal: {NODES_FILE} not found. Aborting.")
        return

    output_nodes_md = []
    all_found_proxies = set()
    table_line_pattern = re.compile(r'^\s*\|.*\|.*\|.*\|(https?://.*)\|')

    for line in lines:
        match = table_line_pattern.match(line)
        if match:
            url = match.group(1).strip()
            proxies = get_proxies_from_url(url)
            status_icon, count = ("✅", len(proxies)) if proxies else ("❌", 0)
            all_found_proxies.update(proxies)
            updated_line = re.sub(r'\|.*\|.*\|', f'| {status_icon} | {count} |', line, count=1)
            output_nodes_md.append(updated_line)
        else:
            output_nodes_md.append(line)

    with open(NODES_FILE, "w", encoding="utf8") as f:
        f.write(''.join(output_nodes_md))
    logging.info(f"{NODES_FILE} has been updated with the latest statuses.")
    
    ss_servers_final = sorted([
        change_shadowsocks_tag(p, NEW_TAG)
        for p in all_found_proxies if p.startswith("ss://")
    ])
    
    logging.info(f"Total unique Shadowsocks servers found: {len(ss_servers_final)}")

    if ss_servers_final:
        # --- بخش اضافه شده برای ساخت فایل‌ها ---
        server_list_content = '\n'.join(ss_servers_final)
        
        # 1. ساخت فایل ss.txt (متن ساده)
        with open(SS_TEXT_FILE, 'w', encoding='utf-8') as f:
            f.write(server_list_content)
        logging.info(f"`{SS_TEXT_FILE}` plain text file created.")
        
        # 2. ساخت فایل ss_sub (اشتراک Base64)
        encoded_sub = base64.b64encode(server_list_content.encode('utf-8')).decode('utf-8')
        with open(SS_SUB_FILE, 'w', encoding='utf-8') as f:
            f.write(encoded_sub)
        logging.info(f"`{SS_SUB_FILE}` subscription file created.")

        update_readme(ss_servers_final)
        send_to_telegram(ss_servers_final)
    else:
        logging.warning("No Shadowsocks servers found after processing all sources.")

if __name__ == "__main__":
    main()
