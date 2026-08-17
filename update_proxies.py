import json
from datetime import datetime
from urllib.parse import quote

VISIBLE_COUNT = 10
SITE_URL = "https://effervescent-clafoutis-1c56fe.netlify.app/"
WORKING_FILE = "working_proxies.json"

def load_working_proxies():
    try:
        with open(WORKING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        proxies = data if isinstance(data, list) else data.get("proxies", [])
        result = []
        for proxy in proxies:
            server = proxy.get("server")
            port = proxy.get("port")
            secret = proxy.get("secret")
            if not server or not port or not secret:
                continue
            if not proxy.get("tg_link"):
                proxy["tg_link"] = f"tg://proxy?server={server}&port={port}&secret={secret}"
            result.append(proxy)
        result.sort(key=lambda x: float(x.get("rtt_ms", 999999)))
        return result
    except Exception as exc:
        print("Ошибка чтения working_proxies.json:", exc)
        return []

def make_html(proxies):
    blocks = ""
    for i, proxy in enumerate(proxies, 1):
        hidden = " extra-proxy hidden" if i > VISIBLE_COUNT else ""
        try:
            rtt = f"{float(proxy.get('rtt_ms', 0)):.0f} мс"
        except Exception:
            rtt = "проверен"
        blocks += f"""
        <div class="proxy{hidden}">
            <div class="proxy-top">
                <div class="proxy-title">Подключение №{i}</div>
                <div class="latency">✅ {rtt}</div>
            </div>
            <a class="connect" href="{proxy['tg_link']}">Подключить</a>
        </div>
        """

    empty = "" if proxies else """
    <div class="empty">
        Сейчас нет доступных подключений.
    </div>
    """

    show_more = ""
    if len(proxies) > VISIBLE_COUNT:
        show_more = """
        <button class="show-more-btn" onclick="toggleExtraProxies()">
            Показать ещё
        </button>
        """

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=" + quote(SITE_URL, safe="")

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Подключение</title>
<style>
body {{ margin:0; padding:20px; font-family:Arial,sans-serif; background:#f1f3f5; }}
.container {{ max-width:540px; margin:30px auto; padding:25px; background:white; border-radius:16px; box-shadow:0 5px 20px rgba(0,0,0,0.12); }}
h1 {{ text-align:center; font-size:26px; margin-top:0; margin-bottom:10px; }}
.description {{ text-align:center; color:#555; line-height:1.5; margin-bottom:12px; }}
.hint {{ text-align:center; background:#eef6ff; color:#1f4d7a; padding:12px; border-radius:10px; margin-bottom:22px; font-size:15px; }}
.summary {{ text-align:center; color:#4b5563; font-size:14px; margin-bottom:18px; }}
.proxy {{ margin:14px 0; padding:15px; background:#f7f7f7; border-radius:10px; }}
.proxy-top {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:10px; }}
.proxy-title {{ font-weight:bold; font-size:19px; }}
.latency {{ color:#16803c; font-size:14px; white-space:nowrap; }}
.connect {{ display:block; padding:14px; color:white; background:#229ed9; border-radius:9px; text-decoration:none; text-align:center; font-size:17px; font-weight:bold; }}
.hidden {{ display:none; }}
.show-more-btn {{ display:block; width:100%; margin-top:18px; padding:14px; border:none; border-radius:9px; background:#4b5563; color:white; font-size:16px; font-weight:bold; cursor:pointer; }}
.empty {{ padding:20px; text-align:center; background:#fff4e5; color:#784900; border-radius:10px; }}
.qr-block {{ margin-top:28px; text-align:center; padding-top:20px; border-top:1px solid #e5e7eb; }}
.qr-title {{ font-weight:bold; margin-bottom:10px; }}
.qr-subtitle {{ color:#666; font-size:14px; margin-bottom:12px; }}
.qr-block img {{ width:220px; max-width:100%; border-radius:10px; background:white; }}
.updated {{ margin-top:22px; text-align:center; color:#777; font-size:13px; }}
</style>
</head>
<body>
<div class="container">
<h1>Подключение</h1>
<div class="description">Здесь отображаются только проверенные подключения.</div>
<div class="hint"></div>
<div class="summary">Доступных подключений: {len(proxies)}</div>
{blocks}
{empty}
{show_more}
<div class="qr-block">
<div class="qr-title">QR-код страницы</div>
<div class="qr-subtitle">Отсканируйте, чтобы открыть страницу на телефоне</div>
<img src="{qr_url}" alt="QR-код страницы">
</div>
<div class="updated">Страница обновлена: {now}</div>
</div>
<script>
function toggleExtraProxies() {{
  const extra = document.querySelectorAll(".extra-proxy");
  const button = document.querySelector(".show-more-btn");
  const hiddenNow = Array.from(extra).some(item => item.classList.contains("hidden"));
  extra.forEach(item => item.classList.toggle("hidden"));
  if (button) button.textContent = hiddenNow ? "Скрыть" : "Показать ещё";
}}
</script>
</body>
</html>"""

def main():
    proxies = load_working_proxies()
    html = make_html(proxies)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Доступных подключений на странице: {len(proxies)}")
    print("index.html обновлён из working_proxies.json")

if __name__ == "__main__":
    main()
