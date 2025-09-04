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
SS_FILE = 'ss'
SS_SUB_FILE = 'ss_sub'
NEW_TAG = 'proxyfig'
REQUEST_TIMEOUT = 5

# These variables are read from GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.environ.get('TELEGRAM_CHANNEL_ID')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_proxies_from_url(url):
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200: return []
        content = response.text
        try:
            proxies = base64.b64decode(content).decode('utf-8').splitlines()
        except:
            proxies = content.splitlines()
        return [p.strip() for p in proxies if p.strip().startswith(('ss://', 'vmess://', 'vless://', 'trojan://', 'ssr://'))]
    except Exception as e:
        logging.error(f"Error fetching {url}: {e}")
        return []

def change_shadowsocks_tag(ss_link, new_tag):
    try:
        return f"{ss_link.split('#', 1)[0]}#{quote(new_tag)}"
    except:
        return ss_link

def update_readme(servers):
    """Updates the README.md file without the full server list."""
    if not servers: return
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    repo_url = f"https://raw.githubusercontent.com/{os.environ.get('GITHUB_REPOSITORY', '')}/main"
    content = (
        f"# Shadowsocks Servers\n\n"
        f"**Tag:** `{NEW_TAG}`\n"
        f"**Total Servers:** `{len(servers)}`\n"
        f"**Last Updated (UTC):** `{now_utc}`\n\n"
        f"**Subscription Link (Base64):**\n"
        f"```\n{repo_url}/{SS_SUB_FILE}\n```\n\n"
        f"**Plain Text Link:**\n"
        f"```\n{repo_url}/{SS_FILE}\n```\n"
    )
    with open(README_FILE, 'w', encoding='utf-8') as f: f.write(content)
    logging.info(f"Successfully updated {README_FILE}")

def send_to_telegram(servers):
    """Sends a notification with the GitHub page link to the Telegram channel."""
    if not all([servers, TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID]): return
    repo_name = os.environ.get('GITHUB_REPOSITORY')
    if not repo_name:
        logging.error("GITHUB_REPOSITORY env var not set.")
        return
        
    # --- این خط برای ساخت لینک جدید تغییر کرده است ---
    github_page_link = f"https://github.com/{repo_name}/blob/main/{SS_FILE}"
    # --- پایان تغییر ---

    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    message_text = (
        f"🚀 **Shadowsocks Servers Update** 🚀\n\n"
        f"✅ `{len(servers)}` new servers are available!\n"
        f"🏷️ **Tag:** `{NEW_TAG}`\n"
        f"⏰ **Updated (UTC):** `{now_utc}`\n\n"
        f"**Click the link below to view the servers on GitHub:**\n"
        f"👇👇👇\n"
        f"🔗 [**View Server List on GitHub ({SS_FILE})**]({github_page_link})\n\n"
        f"Or copy this URL:\n```\n{github_page_link}\n```"
    )
    payload = {'chat_id': TELEGRAM_CHANNEL_ID, 'text': message_text, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json=payload, timeout=10)
        if response.status_code == 200: logging.info("Successfully sent the link to Telegram.")
        else: logging.error(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        logging.error(f"Error connecting to Telegram API: {e}")

def main():
    try:
        with open(NODES_FILE, 'r', encoding="utf8") as f: lines = f.readlines()
    except FileNotFoundError:
        logging.error(f"Fatal: {NODES_FILE} not found."); return

    output_nodes_md, all_found_proxies = [], set()
    pattern = re.compile(r'^\s*\|.*\|.*\|.*\|(https?://.*)\|')
    for line in lines:
        match = pattern.match(line)
        if match:
            url = match.group(1).strip()
            proxies = get_proxies_from_url(url)
            status, count = ("✅", len(proxies)) if proxies else ("❌", 0)
            all_found_proxies.update(proxies)
            updated_line = re.sub(r'\|.*\|.*\|', f'| {status} | {count} |', line, count=1)
            output_nodes_md.append(updated_line)
        else:
            output_nodes_md.append(line)
    with open(NODES_FILE, "w", encoding="utf8") as f: f.write(''.join(output_nodes_md))
    
    ss_servers_final = sorted([change_shadowsocks_tag(p, NEW_TAG) for p in all_found_proxies if p.startswith("ss://")])
    logging.info(f"Total unique Shadowsocks servers found: {len(ss_servers_final)}")

    if ss_servers_final:
        content = '\n'.join(ss_servers_final)
        # 1. Create 'ss' file (plain text)
        with open(SS_FILE, 'w', encoding='utf-8') as f: f.write(content)
        logging.info(f"`{SS_FILE}` file created.")
        # 2. Create 'ss_sub' file (Base64 subscription)
        with open(SS_SUB_FILE, 'w', encoding='utf-8') as f: f.write(base64.b64encode(content.encode()).decode())
        logging.info(f"`{SS_SUB_FILE}` subscription file created.")
        
        update_readme(ss_servers_final)
        send_to_telegram(ss_servers_final)
    else:
        logging.warning("No Shadowsocks servers found.")

if __name__ == "__main__":
    main()        content = '\n'.join(ss_servers_final)
        # 1. Create 'ss' file (plain text)
        with open(SS_FILE, 'w', encoding='utf-8') as f: f.write(content)
        logging.info(f"`{SS_FILE}` file created.")
        # 2. Create 'ss_sub' file (Base64 subscription)
        with open(SS_SUB_FILE, 'w', encoding='utf-8') as f: f.write(base64.b64encode(content.encode()).decode())
        logging.info(f"`{SS_SUB_FILE}` subscription file created.")
        update_readme(ss_servers_final)
        send_to_telegram(ss_servers_final)
    else:
        logging.warning("No Shadowsocks servers found.")

if __name__ == "__main__":
    main()
