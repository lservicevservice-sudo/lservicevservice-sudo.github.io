import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, quote

import requests
from bs4 import BeautifulSoup
from mtproxy_checker import CheckOptions, check_proxy


CHANNEL_URL = "https://t.me/s/mtp4tg"
MAX_CANDIDATES = 50
MAX_WORKING = 30
VISIBLE_COUNT = 10
SITE_URL = "https://lservicevservice-sudo.github.io/"

CONNECT_TIMEOUT = 3.0
RESPONSE_TIMEOUT = 3.0
CHECK_WORKERS = 10

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def collect_candidates():
    response = requests.get(
        CHANNEL_URL,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    candidates = []
    seen = set()

    messages = soup.select(".tgme_widget_message_wrap")

    # Сначала самые свежие сообщения
    for message in reversed(messages):
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

            https_link = (
                "https://t.me/proxy?"
                f"server={server}&"
                f"port={port}&"
                f"secret={secret}"
            )

            tg_link = (
                "tg://proxy?"
                f"server={server}&"
                f"port={port}&"
                f"secret={secret}"
            )

            candidates.append({
                "server": server,
                "port": port,
                "secret": secret,
                "check_link": https_link,
                "link": tg_link,
            })

            if len(candidates) >= MAX_CANDIDATES:
                return candidates

    return candidates


def verify_one(proxy):
    try:
        result = check_proxy(
            proxy["check_link"],
            CheckOptions(
                connect_timeout=CONNECT_TIMEOUT,
                response_timeout=RESPONSE_TIMEOUT,
            ),
        )

        if not result.ok:
            return None

        checked = proxy.copy()
        checked["rtt_ms"] = round(float(result.rtt_ms), 1)
        checked["mode"] = str(result.mode)
        checked["dc"] = int(result.dc)

        return checked

    except Exception as exc:
        print(
            f"Ошибка проверки {proxy['server']}:{proxy['port']}: {exc}"
        )
        return None


def verify_candidates(candidates):
    working = []

    with ThreadPoolExecutor(max_workers=CHECK_WORKERS) as executor:
        futures = {
            executor.submit(verify_one, proxy): proxy
            for proxy in candidates
        }

        for future in as_completed(futures):
            checked = future.result()

            if checked is not None:
                working.append(checked)

    # Самые быстрые — первыми
    working.sort(key=lambda x: x["rtt_ms"])

    return working[:MAX_WORKING]


def make_html(working):
    buttons = ""

    for i, proxy in enumerate(working, 1):
        hidden_class = ""

        if i > VISIBLE_COUNT:
            hidden_class = " extra-proxy hidden"

        buttons += f"""
        <div class="proxy{hidden_class}">
            <div class="proxy-top">
                <div class="proxy-title">Прокси №{i}</div>
                <div class="latency">✅ {proxy['rtt_ms']:.0f} мс</div>
            </div>

            <a class="connect" href="{proxy['link']}">
                Подключить
            </a>
        </div>
        """

    if working:
        empty_message = ""
    else:
        empty_message = """
        <div class="empty">
            Сейчас не найдено ни одного прокси,
            прошедшего проверку Telegram.
            Список будет проверен снова автоматически.
        </div>
        """

    show_more_html = ""

    if len(working) > VISIBLE_COUNT:
        show_more_html = """
        <button class="show-more-btn" onclick="toggleExtraProxies()">
            Показать ещё
        </button>
        """

    now_local = datetime.now().astimezone()
    now_text = now_local.strftime("%d.%m.%Y %H:%M")

    qr_url = (
        "https://api.qrserver.com/v1/create-qr-code/"
        "?size=220x220&data="
        + quote(SITE_URL, safe="")
    )

    return f"""<!DOCTYPE html>
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
    max-width: 540px;
    margin: 30px auto;
    padding: 25px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.12);
}}

h1 {{
    text-align: center;
    font-size: 26px;
    margin-top: 0;
    margin-bottom: 10px;
}}

.description {{
    text-align: center;
    color: #555;
    line-height: 1.5;
    margin-bottom: 12px;
}}

.hint {{
    text-align: center;
    background: #eef6ff;
    color: #1f4d7a;
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 22px;
    font-size: 15px;
}}

.summary {{
    text-align: center;
    color: #4b5563;
    font-size: 14px;
    margin-bottom: 18px;
}}

.proxy {{
    margin: 14px 0;
    padding: 15px;
    background: #f7f7f7;
    border-radius: 10px;
}}

.proxy-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}}

.proxy-title {{
    font-weight: bold;
    font-size: 19px;
}}

.latency {{
    color: #16803c;
    font-size: 14px;
    white-space: nowrap;
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

.hidden {{
    display: none;
}}

.show-more-btn {{
    display: block;
    width: 100%;
    margin-top: 18px;
    padding: 14px;
    border: none;
    border-radius: 9px;
    background: #4b5563;
    color: white;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}}

.empty {{
    padding: 20px;
    text-align: center;
    background: #fff4e5;
    color: #784900;
    border-radius: 10px;
}}

.qr-block {{
    margin-top: 28px;
    text-align: center;
    padding-top: 20px;
    border-top: 1px solid #e5e7eb;
}}

.qr-title {{
    font-weight: bold;
    margin-bottom: 10px;
}}

.qr-subtitle {{
    color: #666;
    font-size: 14px;
    margin-bottom: 12px;
}}

.qr-block img {{
    width: 220px;
    max-width: 100%;
    border-radius: 10px;
    background: white;
}}

.updated {{
    margin-top: 22px;
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
        Здесь отображаются только прокси,
        прошедшие проверку соединения с Telegram.
    </div>

    <div class="hint">
        Если первый не подключился у вас — попробуйте следующий.
    </div>

    <div class="summary">
        Проверено кандидатов: {MAX_CANDIDATES} ·
        Рабочих найдено: {len(working)}
    </div>

    {buttons}

    {empty_message}

    {show_more_html}

    <div class="qr-block">
        <div class="qr-title">QR-код страницы</div>

        <div class="qr-subtitle">
            Отсканируйте, чтобы открыть страницу на телефоне
        </div>

        <img src="{qr_url}" alt="QR-код страницы">
    </div>

    <div class="updated">
        Последняя проверка: {now_text}
    </div>

</div>

<script>
function toggleExtraProxies() {{
    const extra = document.querySelectorAll(".extra-proxy");
    const button = document.querySelector(".show-more-btn");

    const currentlyHidden =
        Array.from(extra).some(item => item.classList.contains("hidden"));

    extra.forEach(item => item.classList.toggle("hidden"));

    if (button) {{
        button.textContent =
            currentlyHidden ? "Скрыть" : "Показать ещё";
    }}
}}
</script>

</body>
</html>
"""


def main():
    candidates = collect_candidates()

    print(f"Получено кандидатов: {len(candidates)}")

    working = verify_candidates(candidates)

    print(f"Прошли MTProto-проверку: {len(working)}")

    result = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(candidates),
        "working_count": len(working),
        "proxies": working,
    }

    with open("proxies.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    html = make_html(working)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("proxies.json и index.html обновлены")


if __name__ == "__main__":
    main()
