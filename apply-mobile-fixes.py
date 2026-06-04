#!/usr/bin/env python3
"""
Впаивает mobile-fixes.css + мобильный JS в index.html лендинга «Мамина неделька».

ЗАЧЕМ ТАК СЛОЖНО: экспорт Claude Design — самосборный бандл. На загрузке он
ПЕРЕСОЗДАЁТ весь документ из сериализованной (escaped) строки внутри себя, поэтому
обычные <style>/<script> в <head>/<body> стираются и НЕ применяются. Единственный
надёжный способ — вписать наше ВНУТРЬ этой строки:
  • CSS  — перед экранированным </style>  (`<\\u002Fstyle>`), что перед </head>…#root
  • JS   — перед экранированным </body>   (`<\\u002Fbody>`)

JS — делегированный слушатель на document (скролл страницы наверх при клике по .tab),
переживает ре-рендер.

ИСПОЛЬЗОВАНИЕ (после нового экспорта из Claude Design):
    python3 apply-mobile-fixes.py
Затем: git commit/push + cp index.html в /srv/maminanedelka_www/ (см. runbook 12).
"""
import re, sys, pathlib

here = pathlib.Path(__file__).parent
html_path = here / "index.html"

# --- CSS ---
raw = (here / "mobile-fixes.css").read_text(encoding="utf-8")
css = re.sub(r"</?style[^>]*>", "", raw)
css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
css = re.sub(r"\s+", " ", css).strip()
css_inject = "/*MFX*/" + css

# --- JS: скролл наверх при смене вкладки (закрывающий тег экранируем как в бандле) ---
js = ("<script>/*MFXJS*/document.addEventListener('click',function(e){"
      "var t=e.target&&e.target.closest&&e.target.closest('.tab');"
      "if(t){setTimeout(function(){window.scrollTo(0,0);},30);}},true);"
      "<\\u002Fscript>")

data = html_path.read_text(encoding="utf-8")
before = len(data)

# убрать прошлые вставки (идемпотентность)
data = re.sub(r"/\*MFX\*/.*?(?=<\\u002Fstyle>)", "", data, flags=re.S)
data = re.sub(r"<script>/\*MFXJS\*/.*?<\\u002Fscript>", "", data, flags=re.S)

# CSS -> перед escaped </style> (тем, после которого идёт head/root)
sidx = [m.start() for m in re.finditer(re.escape("<\\u002Fstyle>"), data)]
if not sidx:
    sys.exit("НЕ НАЙДЕН escaped </style> — структура бандла изменилась, проверь вручную")
st = next((i for i in sidx if "head" in data[i:i+120] and "root" in data[i:i+160]), sidx[-1])
data = data[:st] + css_inject + data[st:]

# JS -> перед escaped </body>
bidx = [m.start() for m in re.finditer(re.escape("<\\u002Fbody>"), data)]
if not bidx:
    sys.exit("НЕ НАЙДЕН escaped </body> — проверь вручную")
data = data[:bidx[-1]] + js + data[bidx[-1]:]

html_path.write_text(data, encoding="utf-8")
d = html_path.read_text(encoding="utf-8")
print(f"OK; размер {before} -> {len(d)}; CSS-маркер: {'/*MFX*/' in d}; JS-маркер: {'/*MFXJS*/' in d}")
print("Дальше: git add/commit/push + cp index.html /srv/maminanedelka_www/")
