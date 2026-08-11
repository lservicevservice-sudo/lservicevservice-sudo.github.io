import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

CHANNEL_URL = "https://t.me/s/mtp4tg"
MAX_PROXIES = 30

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(CHANNEL_URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

proxies = []
seen = set()

# Telegram показывает сообщения от старых к новым.
# Переворачиваем список, чтобы сначала были самые свежие.
messages = soup.select(".tgme_widget_message_wrap")

for message in reversed(messages):

    text = message.get_text(" ", strip=True).lower()

    if "#online" in text:
        status = "online"
    elif "#unstable" in text:
        status = "unstable"
    elif "#offline" in text:
        status = "offline"
    else:
        status = "unknown"

    links = message.find_all("a", href=True)

    for link in links:
        href = link["href"]

        if "t.me/proxy?" not in href:
            continue

        parsed = urlparse(href)
        params = parse_qs(parsed.query)

        server = params.get("server", [None])[0]
        port = params.get("port", [None])[0]
        secret = params.get("secret", [None])[0]

        if not server or not port or not secret:
            continue

        key = (server, port, secret)

        if key in seen:
            continue

        seen.add(key)

        tg_link = (
            f"tg://proxy?"
            f"server={server}&"
            f"port={port}&"
            f"secret={secret}"
        )

        proxies.append({
            "server": server,
            "port": port,
            "secret": secret,
            "status": status,
            "link": tg_link
        })

        if len(proxies) >= MAX_PROXIES:
            break

    if len(proxies) >= MAX_PROXIES:
        break


result = {
    "updated": datetime.now(timezone.utc).isoformat(),
    "source": "@mtp4tg",
    "count": len(proxies),
    "proxies": proxies
}

with open("proxies.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Сохранено прокси: {len(proxies)}")
