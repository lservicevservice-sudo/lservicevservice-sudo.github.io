.updated {{
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
