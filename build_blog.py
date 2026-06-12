#!/usr/bin/env python3
"""Сборка блога maminanedelka.ru/blog/ из SEO-статей mamina_marketing.

Источник: ../mamina_marketing/vc_content/content/seo/A-*.md (формат: 3 строки
keyword:/week_ref:/intent:, пустая, заголовок, тело абзацами; подзаголовок =
однострочный блок без точки на конце; в конце CTA-абзац со ссылкой на бота и
блок «ФОТО-ИДЕИ:», который в вёрстку не идёт).

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
    ("Беременность по неделям", ["12-nedelya", "20-nedelya", "30-nedelya"]),
    ("Обследования и анализы", ["analizy", "skrining", "vtoroy-skrining", "uzi-grafik"]),
    ("Самочувствие и тело", ["toksikoz", "oteki", "pribavka-vesa", "pitanie",
                             "sheveleniya-nachalo", "schitat-sheveleniya"]),
    ("Подготовка к родам", ["rodom", "podgotovka-k-rodam", "predvestniki", "shvatki"]),
    ("Практическое", ["dekret", "sravnenie-prilozheniy"]),
]
FALLBACK_SECTION = "Практическое"

CSS = """
:root{--ink:#2A1B47;--muted:#8A7FA0;--accent:#7A65C2;--soft:#E6DFFA;--line:#DDD1F4;--bg:#FAFAFD}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font-family:Manrope,-apple-system,'Segoe UI',Roboto,sans-serif;line-height:1.65;font-size:17px}
a{color:var(--accent)}
.top{display:flex;align-items:center;gap:10px;max-width:760px;margin:0 auto;padding:14px 20px}
.top img{width:30px;height:30px;border-radius:8px}
.top .brand{font-weight:800;color:var(--ink);text-decoration:none;font-size:17px}
.top nav{margin-left:auto;display:flex;gap:14px;align-items:center}
.top nav a{text-decoration:none;font-weight:600;font-size:15px;white-space:nowrap}
.btn{display:inline-block;background:var(--accent);color:#fff!important;text-decoration:none;
font-weight:700;padding:9px 16px;border-radius:12px;font-size:15px}
.wrap{max-width:680px;margin:0 auto;padding:8px 20px 48px}
.crumb{font-size:14px;margin:10px 0 0}.crumb a{text-decoration:none;font-weight:600}
h1{font-size:30px;line-height:1.25;letter-spacing:-.3px;margin:14px 0 6px;font-weight:800}
.meta{color:var(--muted);font-size:14px;margin:0 0 18px}
h2{font-size:21px;margin:30px 0 8px;font-weight:800;letter-spacing:-.2px}
p{margin:0 0 14px}
.cta{background:var(--soft);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin:30px 0}
.cta p{margin:0 0 12px;font-size:16px}
.rel{margin-top:38px;border-top:1px solid var(--line);padding-top:18px}
.rel h2{margin-top:0;font-size:18px}
.card{display:block;background:#fff;border:1px solid var(--line);border-radius:14px;
padding:14px 16px;margin:0 0 10px;text-decoration:none;color:var(--ink)}
.card b{display:block;font-size:16px;line-height:1.4}
.card span{color:var(--muted);font-size:14px}
.chip{display:inline-block;background:var(--soft);color:var(--accent);border-radius:999px;
padding:1px 10px;font-size:12.5px;font-weight:700;margin-bottom:6px}
.hero{margin:18px 0 8px}.hero p{color:var(--muted);font-size:16px}
.sec{margin:26px 0 4px;font-size:14px;letter-spacing:.06em;text-transform:uppercase;
color:var(--muted);font-weight:800}
footer{border-top:1px solid var(--line);margin-top:44px;padding:20px;background:#fff}
footer .in{max-width:680px;margin:0 auto;font-size:13.5px;color:var(--muted)}
footer a{font-weight:600}
@media(max-width:480px){h1{font-size:25px}.top nav a.plain{display:none}}
"""

HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="Мамина неделька">
<meta property="og:locale" content="ru_RU">
<meta property="og:type" content="{ogtype}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{base}/blog/assets/logo-96.png">
<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{css}</style>
{jsonld}
</head>
<body>
<header class="top">
  <a class="brand" href="https://maminanedelka.ru/" style="display:flex;align-items:center;gap:10px">
    <img src="assets/logo-96.png" alt="Мамина неделька"> Мамина неделька</a>
  <nav>
    <a class="plain" href="index.html">Блог</a>
    <a class="btn" href="{bot}">Открыть бота</a>
  </nav>
</header>
<div class="wrap">
"""

FOOT = """</div>
<footer><div class="in">
<p>Материалы блога — ориентиры для спокойствия, а не медицинские рекомендации.
Решения о вашем здоровье и здоровье малыша принимает ваш врач.</p>
<p><a href="https://maminanedelka.ru/">Мамина неделька</a> — гид по беременности в Telegram ·
<a href="{bot}">открыть бота</a> · поддержка:
<a href="https://t.me/mamina_nedelka_support_bot">@mamina_nedelka_support_bot</a></p>
</div></footer>
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
    return {"slug": slug, "title": title, "keyword": meta.get("keyword", ""),
            "week": int(week_digits.group()) if week_digits else 0, "desc": desc,
            "content": content, "cta": cta}


def cta_html(raw: str) -> str:
    txt = raw.replace("?start=vc_seo", "?start=blog")
    txt = re.sub(r"\s*Посмотреть:\s*\S+\s*$", "", txt)
    txt = re.sub(r"\s*\n\s*", " ", txt).strip()
    return ('<div class="cta"><p>' + esc(txt) + "</p>"
            f'<a class="btn" href="{BOT}">Открыть бота в Telegram</a></div>')


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
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False) + "</script>")


def related(a: dict, arts: list) -> list:
    others = [x for x in arts if x["slug"] != a["slug"]]
    return sorted(others, key=lambda x: abs(x["week"] - a["week"]))[:3]


def render_article(a: dict, arts: list) -> str:
    url = f"{BASE}/blog/{a['slug']}.html"
    parts = [HEAD.format(title=esc(a["title"]) + " — Мамина неделька",
                         desc=esc(a["desc"]), url=url, ogtype="article",
                         base=BASE, css=CSS, bot=BOT,
                         jsonld=jsonld_article(a, url))]
    parts.append('<p class="crumb"><a href="index.html">← Все статьи</a></p>')
    parts.append(f"<h1>{esc(a['title'])}</h1>")
    week = f"Неделя {a['week']} · " if a["week"] else ""
    parts.append(f'<p class="meta">{week}Блог «Маминой недельки»</p>')
    for kind, txt in a["content"]:
        parts.append(f"<h2>{esc(txt)}</h2>" if kind == "h2" else f"<p>{esc(txt)}</p>")
    if a["cta"]:
        parts.append(cta_html(a["cta"]))
    rel = related(a, arts)
    if rel:
        parts.append('<div class="rel"><h2>Ещё по теме</h2>')
        for r in rel:
            chip = f'<span class="chip">неделя {r["week"]}</span>' if r["week"] else ""
            parts.append(f'<a class="card" href="{r["slug"]}.html">{chip}'
                         f"<b>{esc(r['title'])}</b><span>{esc(r['desc'])}</span></a>")
        parts.append("</div>")
    parts.append(FOOT.format(bot=BOT))
    return "\n".join(parts)


def render_index(arts: list) -> str:
    url = f"{BASE}/blog/index.html"
    by_slug = {a["slug"]: a for a in arts}
    placed = set()
    parts = [HEAD.format(
        title="Блог — Мамина неделька: беременность по неделям, анализы, подготовка к родам",
        desc="Спокойные статьи для будущих мам: что происходит по неделям, какие "
             "обследования когда, как подготовиться к родам. Без алармизма, решает врач.",
        url=url, ogtype="website", base=BASE, css=CSS, bot=BOT, jsonld="")]
    parts.append('<div class="hero"><h1>Блог «Маминой недельки»</h1>'
                 "<p>Спокойные статьи для будущих мам: что происходит с малышом по "
                 "неделям, какие обследования когда, как собраться в роддом. "
                 "Ориентиры, а не назначения — решает всегда ваш врач.</p></div>")
    def card(a):
        chip = f'<span class="chip">неделя {a["week"]}</span>' if a["week"] else ""
        return (f'<a class="card" href="{a["slug"]}.html">{chip}'
                f"<b>{esc(a['title'])}</b><span>{esc(a['desc'])}</span></a>")
    for name, slugs in SECTIONS:
        items = [by_slug[s] for s in slugs if s in by_slug]
        placed.update(x["slug"] for x in items)
        if not items:
            continue
        parts.append(f'<p class="sec">{esc(name)}</p>')
        parts.extend(card(a) for a in sorted(items, key=lambda x: x["week"]))
    rest = [a for a in arts if a["slug"] not in placed]
    if rest:
        parts.append(f'<p class="sec">{esc(FALLBACK_SECTION)}</p>')
        parts.extend(card(a) for a in rest)
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
