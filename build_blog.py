#!/usr/bin/env python3
"""Сборка блога maminanedelka.ru/blog/ из SEO-статей mamina_marketing.

Источник: ../mamina_marketing/vc_content/content/seo/A-*.md (формат: 3 строки
keyword:/week_ref:/intent:, пустая, заголовок, тело абзацами; подзаголовок =
однострочный блок без точки на конце; в конце CTA-абзац со ссылкой на бота и
блок «ФОТО-ИДЕИ:», который в вёрстку не идёт).

Дизайн — гибрид «как мини-апп» + фруктовые акценты (выбор Игоря 2026-06-13,
мокапы _probe/sketches/): градиентная шапка, лента недель, статья карточками,
большие полупрозрачные цифры недель, эмодзи-иконки секций.

Выход: blog/<slug>.html (плоские файлы — apex-Caddy отдаёт только реальные
файлы, каталоги проваливаются в SPA-лендинг), blog/index.html, sitemap.xml,
robots.txt. Запуск: python3 build_blog.py [путь-к-папке-статей]
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    ROOT.parent / "mamina_marketing" / "vc_content" / "content" / "seo")
OUT = ROOT / "blog"
BASE = "https://maminanedelka.ru"
BOT = "https://t.me/mamina_nedelka_bot?start=blog"
PUBLISHED = "2026-06-12"
TODAY = date.today().isoformat()
MAX_H2 = 65  # однострочный блок короче этого и без концевой пунктуации = подзаголовок

SECTIONS = [
    ("🤰", "Беременность по неделям", "weeks",
     ["5-nedelya", "6-nedelya", "8-nedelya", "10-nedelya", "12-nedelya",
      "14-nedelya", "16-nedelya", "18-nedelya", "20-nedelya", "22-nedelya",
      "24-nedelya", "26-nedelya", "28-nedelya", "30-nedelya", "32-nedelya",
      "34-nedelya", "36-nedelya", "38-nedelya", "40-nedelya"]),
    ("🩺", "Обследования и анализы", "checkups",
     ["analizy", "skrining", "vtoroy-skrining", "uzi-grafik"]),
    ("💛", "Самочувствие и тело", "feel",
     ["toksikoz", "oteki", "pribavka-vesa", "pitanie", "sheveleniya-nachalo",
      "schitat-sheveleniya", "kogda-viden-zhivot", "bessonnitsa", "prostuda",
      "izzhoga", "zapor", "bolit-poyasnitsa", "vydeleniya"]),
    ("🎒", "Подготовка к родам", "birth",
     ["rodom", "podgotovka-k-rodam", "predvestniki", "shvatki"]),
    ("📱", "Практическое", "misc",
     ["dekret", "perelyoty", "krasit-volosy", "mozhno-li-kofe",
      "sravnenie-prilozheniy"]),
]
SECTION_OF = {slug: name for _, name, _, slugs in SECTIONS for slug in slugs}
FALLBACK_SECTION = ("📌", "Ещё статьи")

# Эмодзи-иконка статьи (карточки индекса, шапка статьи, related)
EMOJI = {
    "5-nedelya": "🍊", "6-nedelya": "🌱", "8-nedelya": "🫐", "10-nedelya": "🍓",
    "12-nedelya": "🍑", "14-nedelya": "🍋", "16-nedelya": "🥑", "18-nedelya": "🫑",
    "20-nedelya": "🍌", "22-nedelya": "🥭", "24-nedelya": "🌽", "26-nedelya": "🥒",
    "28-nedelya": "🍆", "30-nedelya": "🥥", "32-nedelya": "🍈", "34-nedelya": "🍈",
    "36-nedelya": "🥭", "38-nedelya": "🎃", "40-nedelya": "🍉",
    "kogda-viden-zhivot": "🤰", "bessonnitsa": "😴", "perelyoty": "✈️",
    "krasit-volosy": "💇‍♀️", "prostuda": "🤧", "izzhoga": "🔥", "zapor": "🌿",
    "bolit-poyasnitsa": "🧘", "mozhno-li-kofe": "☕", "vydeleniya": "🤍",
    "analizy": "🩺", "skrining": "🔬", "vtoroy-skrining": "🔍", "uzi-grafik": "📅",
    "toksikoz": "🍵", "oteki": "💧", "pribavka-vesa": "⚖️", "pitanie": "🥗",
    "sheveleniya-nachalo": "🦋", "schitat-sheveleniya": "🦶",
    "rodom": "🎒", "podgotovka-k-rodam": "📋", "predvestniki": "⏰", "shvatki": "🌊",
    "dekret": "📄", "sravnenie-prilozheniy": "📱",
}
ICON_BG = ["i-lav", "i-peach", "i-pink", "i-blue"]

# Эмодзи подзаголовков внутри статьи — по ключевым словам (первое совпадение)
H2_EMOJI = [
    ("малыш", "👶"), ("ребён", "👶"), ("мам", "💛"), ("врач", "🩺"), ("анализ", "🩺"),
    ("скрининг", "🔬"), ("узи", "🔍"), ("сумк", "🎒"), ("документ", "📄"),
    ("чек-лист", "✅"), ("итог", "✅"), ("не стоит", "⚠️"), ("ошибк", "⚠️"),
    ("пита", "🥗"), ("еда", "🥗"), ("сон", "😴"), ("шевел", "🦋"), ("вес", "⚖️"),
    ("отек", "💧"), ("отёк", "💧"), ("дом", "🏠"), ("быт", "🏠"), ("настро", "🌿"),
    ("когда", "⏰"), ("срок", "📅"), ("недел", "📅"), ("зачем", "💡"), ("вопрос", "💬"),
]


def h2_icon(text: str) -> str:
    low = text.lower()
    for key, em in H2_EMOJI:
        if key in low:
            return em
    return "🌸"


CSS = """
:root{--ink:#2A1B47;--muted:#8A7FA0;--accent:#7A65C2;--soft:#E6DFFA;--line:#DDD1F4;--bg:#F4F1FB;
--peach:#FCE6D0;--pink:#F4B6C9;--blue:#C5DAEE;--yellow:#FCDA68;--rose:#D26B82}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Manrope,-apple-system,'Segoe UI',Roboto,sans-serif;background:var(--bg);
color:var(--ink);line-height:1.65;font-size:16.5px}
a{color:var(--accent)}
.app-head{background:linear-gradient(135deg,#7A65C2,#9B85E0 60%,#B8A8E6);color:#fff;
border-radius:0 0 26px 26px;padding:14px 20px 20px}
.app-head.short{padding-bottom:16px}
.bar{display:flex;align-items:center;gap:10px;max-width:760px;margin:0 auto}
.bar img{width:32px;height:32px;border-radius:9px}
.bar .brand{font-weight:800;color:#fff;text-decoration:none;display:flex;align-items:center;gap:10px}
.bar nav{margin-left:auto;display:flex;gap:12px;align-items:center}
.bar nav .plain{color:#fff;text-decoration:none;font-weight:700;font-size:14.5px;white-space:nowrap}
.btn{display:inline-block;background:#fff;color:var(--accent);text-decoration:none;font-weight:800;
padding:9px 16px;border-radius:12px;font-size:14.5px;white-space:nowrap;transition:transform .15s}
.btn:hover{transform:translateY(-1px)}
.btn.grad{background:var(--accent);color:#fff;box-shadow:0 6px 14px rgba(122,101,194,.35)}
.app-head h1{max-width:760px;margin:18px auto 4px;font-size:27px;letter-spacing:-.3px;text-wrap:balance}
.app-head .sub{max-width:760px;margin:0 auto;color:#fffd;font-size:15px;text-wrap:balance}
.weeks{display:flex;gap:8px;overflow-x:auto;max-width:760px;margin:16px auto 0;padding-bottom:4px;
scrollbar-width:none}
.weeks::-webkit-scrollbar{display:none}
.wk{flex:0 0 auto;background:#ffffff22;border:1px solid #ffffff55;color:#fff;border-radius:14px;
padding:7px 12px;text-align:center;font-size:11.5px;font-weight:700;text-decoration:none;white-space:nowrap}
.wk b{display:block;font-size:16px}
.wk:hover{background:#fff;color:var(--accent)}
.wrap{max-width:760px;margin:0 auto;padding:16px 20px 56px}
.sec{display:flex;align-items:center;gap:8px;margin:24px 0 10px;font-weight:800;font-size:17px}
.sec .em{font-size:20px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:600px){.row{grid-template-columns:1fr}.app-head h1{font-size:23px}}
.card{position:relative;display:flex;gap:12px;background:#fff;border-radius:18px;padding:14px;
text-decoration:none;color:var(--ink);box-shadow:0 2px 10px rgba(42,27,71,.06);
transition:transform .12s,box-shadow .12s;overflow:hidden}
.card:hover{transform:translateY(-3px);box-shadow:0 12px 24px rgba(42,27,71,.12)}
.card .bigwk{position:absolute;right:8px;top:-12px;font-size:58px;font-weight:800;
color:var(--accent);opacity:.08;letter-spacing:-2px}
.card .ic{flex:0 0 46px;height:46px;border-radius:14px;display:grid;place-items:center;font-size:24px}
.i-lav{background:var(--soft)}.i-peach{background:var(--peach)}.i-pink{background:var(--pink)}
.i-blue{background:var(--blue)}
.card b{display:block;font-size:15.5px;line-height:1.35;text-wrap:balance}
.card span.d{color:var(--muted);font-size:13.5px;display:block;margin-top:3px}
.crumb{font-size:14px;font-weight:700;margin:2px 0 12px;display:inline-block;text-decoration:none}
.ahead{position:relative;background:#fff;border-radius:22px;padding:22px;
box-shadow:0 2px 10px rgba(42,27,71,.06);overflow:hidden}
.ahead .bigwk{position:absolute;right:14px;top:-18px;font-size:110px;font-weight:800;
color:var(--accent);opacity:.07;letter-spacing:-4px}
.ahead .fr{position:absolute;right:16px;bottom:12px;font-size:38px;transform:rotate(-8deg)}
.chiprow{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}
.chip{background:var(--soft);color:var(--accent);border-radius:999px;padding:3px 12px;
font-size:12.5px;font-weight:800;white-space:nowrap}
.chip.alt{background:var(--peach);color:#B0683A}
.chip.dim{background:var(--bg);color:var(--muted)}
.ahead h1{font-size:24px;line-height:1.3;letter-spacing:-.3px;text-wrap:balance;padding-right:52px}
.block{background:#fff;border-radius:22px;padding:20px 22px;margin-top:14px;
box-shadow:0 2px 10px rgba(42,27,71,.06)}
.block h2{display:flex;align-items:center;gap:10px;font-size:18.5px;margin-bottom:10px;text-wrap:balance}
.block h2 .em{flex:0 0 34px;height:34px;border-radius:11px;display:grid;place-items:center;font-size:18px}
.block p{margin:0 0 13px;font-size:16px}
.block p:last-child{margin:0}
.ctab{background:linear-gradient(135deg,#7A65C2,#9B85E0);border-radius:22px;color:#fff;
padding:22px;margin-top:16px;display:flex;align-items:center;gap:16px}
.ctab .em{font-size:38px}
.ctab b{font-size:17px}
.ctab p{font-size:14.5px;color:#fffd;margin:4px 0 12px}
.rel{margin-top:28px}
.rel .t{font-weight:800;font-size:17px;margin-bottom:10px}
footer{color:var(--muted);font-size:13px;margin-top:34px;text-align:center;padding:0 10px}
footer a{font-weight:700}
html{scroll-behavior:smooth}
.wk.more{background:var(--yellow);border-color:var(--yellow);color:var(--ink)}
.wk.more:hover{background:#fff}
.intro{background:#fff;border-radius:20px;padding:18px 20px;margin-top:2px;
box-shadow:0 2px 10px rgba(42,27,71,.06)}
.intro p{font-size:15.5px;color:var(--ink);margin:0 0 14px}
.hubs{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
@media(min-width:600px){.hubs{grid-template-columns:repeat(5,1fr)}}
.hub{display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center;
background:var(--bg);border:1px solid var(--line);border-radius:16px;padding:12px 8px;
text-decoration:none;color:var(--ink);font-weight:800;font-size:12.5px;line-height:1.3;
transition:transform .12s}
.hub:hover{transform:translateY(-2px);background:var(--soft)}
.hub span{font-size:24px}
"""

HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="yandex-verification" content="5de9122d74676c4f" />
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="Мамина неделька">
<meta property="og:locale" content="ru_RU">
<meta property="og:type" content="{ogtype}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{base}/blog/assets/og-cover.png">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{css}</style>
{jsonld}
</head>
<body>
<div class="app-head{short}">
  <div class="bar">
    <a class="brand" href="https://maminanedelka.ru/"><img src="assets/logo-96.png"
      alt="Мамина неделька"> Мамина неделька</a>
    <nav>
      <a class="plain" href="index.html">Блог</a>
      <a class="btn" href="{bot}">Открыть бота</a>
    </nav>
  </div>
{headextra}</div>
<div class="wrap">
"""

FOOT = """
<footer>
<p>Материалы блога — ориентиры для спокойствия, а не медицинские рекомендации.<br>
Решения о вашем здоровье и здоровье малыша принимает ваш врач.</p>
<p style="margin-top:8px"><a href="https://maminanedelka.ru/">Мамина неделька</a> — гид по
беременности в Telegram · <a href="{bot}">открыть бота</a> · поддержка:
<a href="https://t.me/mamina_nedelka_support_bot">@mamina_nedelka_support_bot</a></p>
</footer>
</div>
</body>
</html>
"""


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    body = text.split("ФОТО-ИДЕИ:")[0]
    blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    meta = dict(re.findall(r"^(keyword|week_ref|intent):\s*(.+)$", blocks[0], re.M))
    title = blocks[1]
    content, cta = [], None
    for b in blocks[2:]:
        if "mamina_nedelka_bot" in b:
            cta = b
        elif "\n" not in b and len(b) <= MAX_H2 and b[-1] not in ".!?…:»)":
            content.append(("h2", b))
        else:
            content.append(("p", re.sub(r"\s*\n\s*", " ", b)))
    slug = re.sub(r"^A-\d{4}-", "", path.stem)
    first_p = next(t for k, t in content if k == "p")
    desc = first_p if len(first_p) <= 158 else first_p[:158].rsplit(" ", 1)[0] + "…"
    week_digits = re.search(r"\d+", meta.get("week_ref", "") or "")
    n_chars = sum(len(t) for k, t in content if k == "p")
    return {"slug": slug, "title": title, "keyword": meta.get("keyword", ""),
            "week": int(week_digits.group()) if week_digits else 0, "desc": desc,
            "content": content, "cta": cta, "mins": max(2, round(n_chars / 1100))}


def plural_stati(n: int) -> str:
    if n % 100 in (11, 12, 13, 14):
        f = "статей"
    elif n % 10 == 1:
        f = "статья"
    elif n % 10 in (2, 3, 4):
        f = "статьи"
    else:
        f = "статей"
    return f"{n} {f}"


def trimester(week: int) -> str:
    if not week:
        return ""
    return ("первый" if week <= 13 else "второй" if week <= 27 else "третий") + " триместр"


def cta_text(raw: str) -> str:
    txt = raw.replace("?start=vc_seo", "?start=blog")
    txt = re.sub(r"\s*Посмотреть:\s*\S+\s*$", "", txt)
    return re.sub(r"\s*\n\s*", " ", txt).strip()


def jsonld_article(a: dict, url: str) -> str:
    data = {
        "@context": "https://schema.org", "@type": "Article",
        "headline": a["title"], "description": a["desc"],
        "inLanguage": "ru", "mainEntityOfPage": url,
        "datePublished": PUBLISHED, "dateModified": TODAY,
        "author": {"@type": "Organization", "name": "Мамина неделька", "url": BASE},
        "publisher": {"@type": "Organization", "name": "Мамина неделька",
                      "logo": {"@type": "ImageObject",
                               "url": f"{BASE}/blog/assets/logo-96.png"}},
    }
    crumbs = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Мамина неделька", "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Блог",
             "item": BASE + "/blog/index.html"},
            {"@type": "ListItem", "position": 3, "name": a["title"], "item": url},
        ],
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False) + "</script>\n"
            + '<script type="application/ld+json">'
            + json.dumps(crumbs, ensure_ascii=False) + "</script>")


def is_week_article(a: dict) -> bool:
    return a["slug"].endswith("-nedelya")


def card(a: dict, i: int) -> str:
    bigwk = f'<span class="bigwk">{a["week"]}</span>' if is_week_article(a) else ""
    return (f'<a class="card" href="{a["slug"]}.html">{bigwk}'
            f'<span class="ic {ICON_BG[i % len(ICON_BG)]}">{EMOJI.get(a["slug"], "🌸")}</span>'
            f'<div><b>{esc(a["title"])}</b>'
            f'<span class="d">{esc(a["desc"])}</span></div></a>')


def related(a: dict, arts: list) -> list:
    others = [x for x in arts if x["slug"] != a["slug"]]
    return sorted(others, key=lambda x: abs(x["week"] - a["week"]))[:3]


def render_article(a: dict, arts: list) -> str:
    url = f"{BASE}/blog/{a['slug']}.html"
    parts = [HEAD.format(title=esc(a["title"]) + " — Мамина неделька",
                         desc=esc(a["desc"]), url=url, ogtype="article", base=BASE,
                         css=CSS, bot=BOT, short=" short", headextra="",
                         jsonld=jsonld_article(a, url))]
    parts.append('<a class="crumb" href="index.html">← Все статьи</a>')
    chips = ""
    if is_week_article(a):
        chips += f'<span class="chip">неделя {a["week"]}</span>'
        chips += f'<span class="chip alt">{trimester(a["week"])}</span>'
    else:
        chips += f'<span class="chip">{esc(SECTION_OF.get(a["slug"], "полезное"))}</span>'
        if a["week"]:
            chips += f'<span class="chip alt">{trimester(a["week"])}</span>'
    chips += f'<span class="chip dim">{a["mins"]} мин</span>'
    bigwk = f'<span class="bigwk">{a["week"]}</span>' if is_week_article(a) else ""
    fruit = f'<span class="fr">{EMOJI.get(a["slug"], "🌸")}</span>'
    parts.append(f'<div class="ahead">{bigwk}{fruit}'
                 f'<div class="chiprow">{chips}</div>'
                 f"<h1>{esc(a['title'])}</h1></div>")
    # тело: интро-абзацы до первого h2 — первая карточка; дальше карточка на главу
    blocks, cur, icon_i = [], [], 0
    cur_head = None
    for kind, txt in a["content"]:
        if kind == "h2":
            if cur or cur_head:
                blocks.append((cur_head, cur))
            cur_head, cur = txt, []
        else:
            cur.append(txt)
    if cur or cur_head:
        blocks.append((cur_head, cur))
    for head, paras in blocks:
        b = ['<div class="block">']
        if head:
            b.append(f'<h2><span class="em {ICON_BG[icon_i % len(ICON_BG)]}">'
                     f"{h2_icon(head)}</span> {esc(head)}</h2>")
            icon_i += 1
        b.extend(f"<p>{esc(t)}</p>" for t in paras)
        b.append("</div>")
        parts.append("".join(b))
    if a["cta"]:
        parts.append('<div class="ctab"><span class="em">🌸</span><div>'
                     "<b>«Мамина неделька» в Telegram</b>"
                     f"<p>{esc(cta_text(a['cta']))}</p>"
                     f'<a class="btn" href="{BOT}">Открыть бота</a></div></div>')
    rel = related(a, arts)
    if rel:
        parts.append('<div class="rel"><div class="t">Ещё по теме</div><div class="row">'
                     + "".join(card(r, i) for i, r in enumerate(rel)) + "</div></div>")
    parts.append(FOOT.format(bot=BOT))
    return "\n".join(parts)


def render_index(arts: list) -> str:
    url = f"{BASE}/blog/index.html"
    by_slug = {a["slug"]: a for a in arts}
    week_arts = sorted((a for a in arts if is_week_article(a)), key=lambda x: x["week"])
    ribbon = "".join(f'<a class="wk" href="{a["slug"]}.html">нед.<b>{a["week"]}</b></a>'
                     for a in week_arts)
    ribbon += f'<a class="wk more" href="{BOT}">все 42<b>в боте →</b></a>'
    headextra = ("<h1>Спокойные статьи для будущих мам</h1>"
                 f'<p class="sub">{plural_stati(len(arts))}: что происходит с малышом по неделям, '
                 "какие обследования когда и как собраться в&nbsp;роддом. Ориентиры, "
                 "а не назначения — решает всегда ваш&nbsp;врач.</p>"
                 f'<div class="weeks">{ribbon}</div>')
    parts = [HEAD.format(
        title="Блог — Мамина неделька: беременность по неделям, анализы, подготовка к родам",
        desc="Спокойные статьи для будущих мам: что происходит по неделям, какие "
             "обследования когда, как подготовиться к родам. Без алармизма, решает врач.",
        url=url, ogtype="website", base=BASE, css=CSS, bot=BOT, short="",
        headextra=headextra, jsonld="")]
    hubs = "".join(f'<a class="hub" href="#{anchor}"><span>{em}</span>{esc(name)}</a>'
                   for em, name, anchor, _ in SECTIONS)
    parts.append('<div class="intro">'
                 "<p><b>Это блог «Маминой недельки»</b> — гида по беременности в Telegram. "
                 "Здесь — спокойные статьи по темам, которые чаще всего тревожат: выбирайте "
                 "раздел, а понедельный календарь (все 42 недели, чек-листы и дневник) "
                 "живёт в&nbsp;боте.</p>"
                 f'<div class="hubs">{hubs}</div></div>')
    placed = set()
    i = 0
    for em, name, anchor, slugs in SECTIONS:
        items = [by_slug[s] for s in slugs if s in by_slug]
        placed.update(x["slug"] for x in items)
        if not items:
            continue
        parts.append(f'<div class="sec" id="{anchor}"><span class="em">{em}</span> '
                     f"{esc(name)}</div>")
        parts.append('<div class="row">'
                     + "".join(card(a, i + j) for j, a in
                               enumerate(sorted(items, key=lambda x: x["week"])))
                     + "</div>")
        i += len(items)
    rest = [a for a in arts if a["slug"] not in placed]
    if rest:
        em, name = FALLBACK_SECTION
        parts.append(f'<div class="sec"><span class="em">{em}</span> {esc(name)}</div>')
        parts.append('<div class="row">' + "".join(card(a, i + j) for j, a in enumerate(rest))
                     + "</div>")
    parts.append(FOOT.format(bot=BOT))
    return "\n".join(parts)


def render_sitemap(arts: list) -> str:
    urls = [(f"{BASE}/", TODAY), (f"{BASE}/blog/index.html", TODAY)]
    urls += [(f"{BASE}/blog/{a['slug']}.html", TODAY) for a in arts]
    items = "".join(
        f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + items + "</urlset>\n")


def main():
    arts = sorted((parse(p) for p in sorted(SRC.glob("A-*.md"))),
                  key=lambda a: a["week"])
    OUT.mkdir(exist_ok=True)
    for a in arts:
        (OUT / f"{a['slug']}.html").write_text(render_article(a, arts), encoding="utf-8")
    (OUT / "index.html").write_text(render_index(arts), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(render_sitemap(arts), encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    print(f"OK: {len(arts)} статей → blog/, + blog/index.html, sitemap.xml, robots.txt")


if __name__ == "__main__":
    main()
