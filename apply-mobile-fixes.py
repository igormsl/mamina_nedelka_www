#!/usr/bin/env python3
"""
Впаивает mobile-fixes.css в index.html лендинга «Мамина неделька».

ЗАЧЕМ ТАК СЛОЖНО: экспорт Claude Design — самосборный бандл. На загрузке он
ПЕРЕСОЗДАЁТ весь документ из сериализованной (escaped) строки внутри себя, поэтому
обычный <style> в <head>/<body> стирается и НЕ применяется. Единственный надёжный
способ — вписать наш CSS ВНУТРЬ этой строки, перед её экранированным </style>
(`<\\u002Fstyle>`), который идёт перед `</head>...<div id="root">`.

ИСПОЛЬЗОВАНИЕ (после нового экспорта из Claude Design):
    python3 apply-mobile-fixes.py            # правит index.html на месте
Затем: git commit/push + cp index.html в /srv/maminanedelka_www/ (см. runbook 12).
"""
import re, sys, pathlib

here = pathlib.Path(__file__).parent
html_path = here / "index.html"
css_path = here / "mobile-fixes.css"

raw = css_path.read_text(encoding="utf-8")
css = re.sub(r"</?style[^>]*>", "", raw)          # снять теги, если есть
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)   # снять комментарии
css = re.sub(r"\s+", " ", css).strip()            # в одну строку (безопасно для JS-строки)
inject = "/*MFX*/" + css                           # маркер для проверки

data = html_path.read_text(encoding="utf-8")
before = len(data)

# 1) убрать прошлую вставку, если была
data = data.replace(inject, "")
data = re.sub(r"/\*MFX\*/.*?(?=<\\u002Fstyle>)", "", data, flags=re.S)  # на случай иной версии

# 2) найти экранированный </style> сериализованного документа (перед head/root) и вставить перед ним
esc = "<\\u002Fstyle>"
idxs = [m.start() for m in re.finditer(re.escape(esc), data)]
if not idxs:
    sys.exit("НЕ НАЙДЕН экранированный </style> — структура бандла изменилась, проверь вручную")
target = next((i for i in idxs if "head" in data[i:i+120] and "root" in data[i:i+160]), idxs[-1])
data = data[:target] + inject + data[target:]

html_path.write_text(data, encoding="utf-8")
ok = "/*MFX*/" in data
print(f"OK впаяно перед поз. {target}; размер {before} -> {len(data)}; маркер: {ok}")
print("Дальше: git add/commit/push + cp index.html /srv/maminanedelka_www/")
