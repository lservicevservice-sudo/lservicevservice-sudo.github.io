[11.08.2026 10:53] System Administrator: import json
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

    for link in message.find_all("a", href=True):

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


# Сохраняем JSON
result = {
    "updated": datetime.now(timezone.utc).isoformat(),
    "source": "@mtp4tg",
    "count": len(proxies),
    "proxies": proxies
}

with open("proxies.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)


# Создаём готовые кнопки
buttons = ""

for i, proxy in enumerate(proxies, 1):

    status = proxy["status"]

    if status == "online":
        status_text = "🟢 Online"
        status_class = "online"
    elif status == "unstable":
        status_text = "🟠 Unstable"
        status_class = "unstable"
    elif status == "offline":
        status_text = "🔴 Offline"
        status_class = "offline"
    else:
        status_text = "⚪ Статус неизвестен"
        status_class = "unknown"

    buttons += f"""
    <div class="proxy">
        <div class="proxy-title">Прокси №{i}</div>
        <div class="status {status_class}">{status_text}</div>
        <a class="connect" href="{proxy['link']}">Подключить</a>
    </div>
    """


now = datetime.now().strftime("%d.%m.%Y %H:%M")

html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Telegram Proxy</title>

<style>

body {{
    margin: 0;
    padding: 20px;
    font-family: Arial, sans-serif;
    background: #f1f3f5;
}}

.container {{
    max-width: 520px;
    margin: 30px auto;
    padding: 25px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.12);
}}

h1 {{
    text-align: center;
    font-size: 25px;
}}

.description {{
    text-align: center;
    color: #555;
    line-height: 1.5;
    margin-bottom: 25px;
}}

.proxy {{
    margin: 14px 0;
    padding: 15px;
    background: #f7f7f7;
    border-radius: 10px;
}}

.proxy-title {{
    font-weight: bold;
    margin-bottom: 5px;
}}

.status {{
    font-size: 14px;
    margin-bottom: 10px;
}}

.online {{
    color: green;
}}

.unstable {{
    color: #d98200;
}}

.offline {{
    color: red;
}}

.unknown {{
    color: #777;
}}

.connect {{
    display: block;
    padding: 14px;
    color: white;
    background: #229ed9;
    border-radius: 9px;
    text-decoration: none;
    text-align: center;
    font-size: 17px;
    font-weight: bold;
}}

.connect:hover {{
    background: #1687bd;
}}
[11.08.2026 10:53] System Administrator: .updated {{
    margin-top: 25px;
    text-align: center;
    color: #777;
    font-size: 13px;
}}

</style>
</head>

<body>

<div class="container">

<h1>Подключение Telegram</h1>

<div class="description">
Выберите один из прокси и нажмите «Подключить».
</div>

{buttons}

<div class="updated">
Автоматическое обновление списка<br>
Источник: @mtp4tg<br>
Последнее обновление: {now}
</div>

</div>

</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"Сохранено прокси: {len(proxies)}")
print("index.html обновлён")
