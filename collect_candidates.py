import json
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

CHANNEL_URLS = [
    "https://t.me/s/mtp4tg",
    "https://t.me/s/oneclickvpnkeys",
]

MAX_CANDIDATES = 50

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def extract_from_channel(channel_url, candidates, seen):
    response = requests.get(
        channel_url,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    messages = soup.select(".tgme_widget_message_wrap")

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

            candidates.append({
                "server": server,
                "port": str(port),
                "secret": secret,
                "https_link": (
                    f"https://t.me/proxy?"
                    f"server={server}&"
                    f"port={port}&"
                    f"secret={secret}"
                ),
                "tg_link": (
                    f"tg://proxy?"
                    f"server={server}&"
                    f"port={port}&"
                    f"secret={secret}"
                )
            })

            if len(candidates) >= MAX_CANDIDATES:
                return


def main():
    candidates = []
    seen = set()

    for channel_url in CHANNEL_URLS:
        if len(candidates) >= MAX_CANDIDATES:
            break

        print(f"Читаю источник: {channel_url}")

        try:
            extract_from_channel(
                channel_url,
                candidates,
                seen
            )
        except Exception as e:
            print(f"Ошибка при чтении {channel_url}: {e}")

    result = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(candidates),
        "proxies": candidates
    }

    with open(
        "candidates.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Сохранено кандидатов: {len(candidates)}")


main()
