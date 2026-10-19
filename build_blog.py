#!/usr/bin/env python3
"""Reproducible stdlib build. Markdown stays in mamina_marketing; no network or bot imports.
Default: local preview. --public-preview is an authorized noindex launch.
--release requires completed reviews; both deployment modes write a separate directory.
"""
import argparse
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'mamina_marketing/blog/content/seo'
BASE = 'https://maminanedelka.ru'
GOOGLE_SITE_VERIFICATION = 'vxssvvoZ0YXI9jxsM1R7xCki1lAf798v34-bzXGFfCU'
BOT = 'https://t.me/mamina_nedelka_bot'
UPDATED = '2026-10-15'
PAGE_UPDATED = {'/about.html': '2026-10-19'}
RELEASE_GATES = ('owner_visual_acceptance', 'owner_details_confirmed',
                 'privacy_and_hosting_review', 'bot_telegram_smoke',
                 'vps_backup_and_rollback_plan', 'public_enable_approved')
PUBLIC_PREVIEW_GATES = ('owner_visual_acceptance', 'vps_backup_and_rollback_plan', 'public_enable_approved')
BLOG_RELEASE_GATES = PUBLIC_PREVIEW_GATES + ('owner_details_confirmed', 'blog_indexing_approved')
CATEGORIES = {'weeks':'По неделям','checkups':'Обследования','feel':'Самочувствие','birth':'К родам','life':'Повседневная жизнь','start':'Начало беременности'}
DEFAULT_GROUPS = {
 'checkups':'analizy skrining vtoroy-skrining uzi-grafik',
 'feel':'toksikoz oteki pribavka-vesa sheveleniya-nachalo schitat-sheveleniya kogda-viden-zhivot bessonnitsa prostuda izzhoga zapor bolit-poyasnitsa vydeleniya trevoga',
 'birth':'rodom podgotovka-k-rodam predvestniki shvatki',
 'life':'dekret perelyoty krasit-volosy mozhno-li-kofe sravnenie-prilozheniy pitanie podderzhka-partnera',
 'start':'akusherskiy-srok polozhitelnyy-test lekarstva',
}

def esc(s): return html.escape(str(s), quote=True)

def site_href(url):
    return url[len(BASE):] if url.startswith(BASE+'/') else url

def inline(text):
    """Small explicit Markdown subset; raw HTML and executable URL schemes are escaped."""
    pieces = []; pos = 0
    for m in re.finditer(r'\[([^\]\n]+)\]\(([^\s)]+)\)', text):
        pieces.append(esc(text[pos:m.start()]))
        label, url = m.groups()
        if url.startswith(('https://','/blog/','/about.html','/editorial.html')):
            pieces.append(f'<a href="{esc(url)}"' + (' rel="noopener noreferrer"' if url.startswith('https://') else '') + f'>{esc(label)}</a>')
        else: pieces.append(esc(m.group()))
        pos = m.end()
    pieces.append(esc(text[pos:])); return ''.join(pieces)

def parse(path):
    raw = path.read_text(encoding='utf-8')
    text = raw.split('ФОТО-ИДЕИ:',1)[0].strip()
    head, sep, rest = text.partition('\n\n')
    if not sep: raise ValueError(f'{path.name}: missing metadata separator')
    meta = dict(line.split(':',1) for line in head.splitlines() if ':' in line)
    meta = {k.strip():v.strip() for k,v in meta.items()}
    blocks = [s.strip() for s in re.split(r'\n\s*\n',rest) if s.strip()]
    slug = re.sub(r'^A-\d{4}-','',path.stem)
    if not re.fullmatch(r'[a-z0-9-]+',slug): raise ValueError(f'Invalid slug: {slug}')
    title = blocks.pop(0).lstrip('# ')
    content = []
    for b in blocks:
        if b.startswith('## '): content.append(('h2',b[3:]))
        elif all(line.startswith('- ') for line in b.splitlines()): content.append(('ul',b))
        else: content.append(('p',re.sub(r'\s*\n\s*',' ',b)))
    intro = next((s for k,s in content if k=='p'),'')
    category = meta.get('category') or ('weeks' if slug.endswith('-nedelya') else next((k for k,v in DEFAULT_GROUPS.items() if slug in v.split()),'life'))
    if category not in CATEGORIES: raise ValueError(f'{slug}: unknown category')
    return dict(slug=slug,id=path.stem[:6].lower().replace('-',''),file=path.name,title=title,
                desc=meta.get('description') or intro[:150].rsplit(' ',1)[0]+'…',intro=intro,
                week=int(meta.get('week_ref','0')) if meta.get('week_ref','').isdigit() else 0,
                category=category,content=content,modified=meta.get('updated',UPDATED),
                status=meta.get('status','specialist_review'),sources=meta.get('sources','').split(),
                related=meta.get('related','').split(),medical=meta.get('medical','true')=='true',
                review_evidence=meta.get('review_evidence',''),
                minutes=max(2,round(sum(len(s.split()) for _,s in content)/180)))

def bot_link(source, placement, label='Открыть в Telegram', light=False):
    source = f'{source}_{placement}'
    assert re.fullmatch(r'[a-z0-9_-]{1,64}',source)
    return f'<a class="btn{" light" if light else ""}" data-bot="{esc(placement)}" href="{BOT}?start={source}">{esc(label)} <span aria-hidden="true">↗</span></a>'

def json_script(data):
    return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False).replace('<','\\u003c')+'</script>'

def blog_indexable(path):
    return bool(re.fullmatch(r'/blog/[a-z0-9-]+\.html', path))

def shell(title, description, path, body, *, source='landing', page='home', schema=None, preview=True, image='life'):
    url=BASE+path
    indexable = not preview or preview == 'blog-release' and blog_indexable(path)
    banner = ('Информационный блог · материалы со ссылками на источники' if indexable else
              'Предварительная версия · материалы проходят проверку' if preview in ('public-preview','blog-release') else
              'Локальный просмотр · материалы готовятся к публикации')
    google_verification = f'<meta name="google-site-verification" content="{esc(GOOGLE_SITE_VERIFICATION)}">' if path == '/' else ''
    schemas=[{'@context':'https://schema.org','@type':'WebSite','@id':BASE+'/#website','name':'Мамина неделька','url':BASE+'/' ,'inLanguage':'ru-RU'}]
    if schema: schemas.extend(schema)
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}">
<meta name="yandex-verification" content="5de9122d74676c4f"><meta name="robots" content="{'index, follow, max-image-preview:large' if indexable else 'noindex, follow'}">{google_verification}
<meta name="referrer" content="strict-origin-when-cross-origin"><meta name="theme-color" content="#faf8f5">
<link rel="canonical" href="{url}"><link rel="icon" href="/blog/assets/favicon-32.png" sizes="32x32" type="image/png">
<meta property="og:site_name" content="Мамина неделька"><meta property="og:locale" content="ru_RU"><meta property="og:type" content="{'article' if re.fullmatch(r'a[0-9]{4}',page) else 'website'}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/assets/illustrations/{image}.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Мамина неделька — {esc(CATEGORIES.get(image,'полезные материалы'))}">
<meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="/assets/site.css"><script defer src="/assets/site.js"></script>
<noscript><style>.filter-panel{{display:none}}@media(max-width:760px){{.topbar{{position:static}}.navrow{{flex-wrap:wrap;padding-bottom:16px}}.menu-toggle{{display:none}}.navlinks{{display:flex;position:static;flex-flow:row wrap;gap:16px;padding:0;box-shadow:none;border:0;width:100%;margin:0}}}}</style></noscript>
{''.join(json_script(s) for s in schemas)}</head><body data-page="{page}">
<a class="skip" href="#main">Перейти к содержанию</a>
{('<div class="preview-label">' + banner + '</div>') if preview else ''}
<header class="topbar"><div class="wrap navrow"><a class="brand" href="/"><img src="/blog/assets/logo-96.png" alt="" width="37" height="37"><span>Мамина неделька<small>рядом с самого начала</small></span></a>
<button class="menu-toggle" aria-label="Меню" aria-expanded="false" aria-controls="navigation">☰</button>
<nav class="navlinks" id="navigation" aria-label="Главная навигация"><a href="/blog/index.html">Блог</a><a href="/#features">О приложении</a><a href="/#plans">Тарифы</a>{bot_link(source,'nav')}</nav></div></header>
{body}
<footer class="footer"><div class="wrap"><div class="footer-top"><a class="brand" href="/">Мамина неделька</a><nav aria-label="Внизу страницы"><a href="/about.html">О проекте и контакты</a><a href="/editorial.html">Как мы пишем</a><a href="/privacy.html">Конфиденциальность</a><a href="https://t.me/mamina_nedelka_support_bot" rel="noreferrer">Поддержка</a></nav></div>
<p>Информационный проект для будущих мам. Статьи и AI-помощник не ставят диагнозы и не заменяют медицинскую помощь. При ухудшении самочувствия обращайтесь к врачу.</p>
<div class="footer-bottom"><span>© 2026 Мамина неделька</span><span>С заботой о вашем времени и внимании</span></div></div></footer></body></html>'''

def card(a, searchable=False):
    extra=f' data-article data-category="{a["category"]}" data-search="{esc(a["title"]+" "+a["desc"])}"' if searchable else ''
    badge=f'<span class="week-badge">{a["week"]}</span>' if a['category']=='weeks' else ''
    return f'''<a class="story" href="/blog/{a['slug']}.html"{extra}><div class="story-art"><img src="/assets/illustrations/{a['category']}.svg" alt="" width="1200" height="630" loading="lazy">{badge}</div><div class="story-body"><span class="label">{CATEGORIES[a['category']]}</span><h3>{esc(a['title'])}</h3><p>{esc(a['desc'])}</p><span class="read">{a['minutes']} мин чтения <span aria-hidden="true">↗</span></span></div></a>'''

def article(a, all_articles, sources, preview):
    source=f'blog_{a["id"]}'
    headings=[]; parts=[]
    intro_removed=False
    for kind,text in a['content']:
        if kind=='p' and not intro_removed:
            intro_removed=True; continue
        if kind=='h2':
            anchor=f'section-{len(headings)+1}'; headings.append((anchor,text)); parts.append(f'<h2 id="{anchor}">{esc(text)}</h2>')
        elif kind=='ul': parts.append('<ul>'+''.join('<li>'+inline(x[2:])+'</li>' for x in text.splitlines())+'</ul>')
        else: parts.append('<p>'+inline(text)+'</p>')
    toc='<aside class="toc" aria-label="Содержание статьи"><b>В этой статье</b><ol>'+''.join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i,t in headings)+'</ol></aside>'
    by_slug={x['slug']:x for x in all_articles}
    related=[by_slug[s] for s in a['related'] if s in by_slug and s!=a['slug']][:3]
    if len(related)<3:
        related += [x for x in all_articles if x['category']==a['category'] and x not in related and x!=a][:3-len(related)]
    refs=''.join(f'<li><a href="{esc(site_href(sources[s]["url"]))}" rel="noreferrer">{esc(sources[s]["title"])}</a> — {esc(sources[s]["scope"])}</li>' for s in a['sources'])
    review = ('Требуется проверка акушером-гинекологом перед публикацией. Ссылки на источники приведены в конце; медицинская рецензия пока не проводилась.' if a['medical'] else 'Редакционный материал подготовлен для приёмки владельцем. Публикация ещё не выполнена.')
    if preview in ('public-preview','blog-release'):
        review = ('Медицинская рецензия пока не проводилась. Материал требует проверки акушером-гинекологом; ссылки на использованные источники приведены в конце.' if a['medical'] else 'Предварительная редакция: материал проходит проверку.')
    note=f'<div class="review-note">{review}</div>' if a['status']!='approved' else '<div class="review-note">Информационный материал. Индивидуальные рекомендации даёт ваш врач.</div>' if a['medical'] else ''
    cta=f'''<section class="article-cta"><h2>Своя неделя — под рукой</h2><p>В «Маминой недельке» можно открыть материалы по сроку и сохранить вопросы к приёму. После перехода нажмите «Старт» в Telegram, откройте приложение и укажите срок. Базовый доступ бесплатный.</p>{bot_link(source,'article_end','Посмотреть свою неделю')}<p class="small">При тревожных симптомах обращайтесь за медицинской помощью; бот не оценивает срочность вашего состояния.</p></section>'''
    body=f'''<main class="wrap" id="main"><nav class="crumbs" aria-label="Хлебные крошки"><a href="/">Главная</a><span>/</span><a href="/blog/index.html">Блог</a><span>/</span><span>{CATEGORIES[a['category']]}</span></nav>
<header class="article-head"><div class="eyebrow">{CATEGORIES[a['category']]}</div><h1>{esc(a['title'])}</h1><p class="lead">{inline(a['intro'])}</p><div class="meta"><span>{a['minutes']} мин чтения</span><span>Редакция текста: <time datetime="{a['modified']}">{a['modified']}</time></span><a href="/editorial.html">Источники и редакционные правила</a></div></header>{note}
<div class="article-layout"><article class="article-body"><img class="article-cover" src="/assets/illustrations/{a['category']}.svg" alt="" width="1200" height="630">{''.join(parts)}
<section class="sources" id="sources"><h2>Источники</h2><p>Сверка доступных материалов: 15 октября 2026. Общие рекомендации зарубежных служб не заменяют российский план наблюдения.</p><ol>{refs}</ol></section>{cta}<a class="back-top" href="#main">↑ К началу статьи</a></article>{toc}</div>
<section class="related"><div class="section-head"><h2>Можно почитать дальше</h2><a href="/blog/index.html">Все материалы →</a></div><div class="story-grid">{''.join(card(x) for x in related)}</div></section></main>'''
    url=BASE+f'/blog/{a["slug"]}.html'
    # No invented doctor, author, first-publication date, ratings or medical review.
    schema=[{'@context':'https://schema.org','@type':'Article','headline':a['title'],'description':a['desc'],'mainEntityOfPage':url,'url':url,'inLanguage':'ru-RU','dateModified':a['modified'],'image':[BASE+f'/assets/illustrations/{a["category"]}.png'],'publisher':{'@type':'Organization','name':'Мамина неделька','url':BASE+'/'},'citation':[sources[s]['url'] for s in a['sources']]}, {'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Главная','item':BASE+'/'},{'@type':'ListItem','position':2,'name':'Блог','item':BASE+'/blog/index.html'},{'@type':'ListItem','position':3,'name':a['title'],'item':url}]}]
    return shell(a['title']+' | Мамина неделька',a['desc'],f'/blog/{a["slug"]}.html',body,source=source,page=a['id'],schema=schema,preview=preview,image=a['category'])

def catalogue(arts,preview):
    filters='<button class="filter" data-filter="all" aria-pressed="true">Все темы</button>'+''.join(f'<button class="filter" data-filter="{k}" aria-pressed="false">{v}</button>' for k,v in CATEGORIES.items())
    featured=['polozhitelnyy-test','rodom','trevoga','skrining','akusherskiy-srok','podderzhka-partnera']
    ordered=sorted(arts,key=lambda a:(featured.index(a['slug']) if a['slug'] in featured else 10,a['category']=='weeks',a['week'],a['title']))
    body=f'''<main class="wrap" id="main"><section class="blog-intro"><div class="eyebrow">Библиотека будущей мамы</div><h1>Есть вопрос.<br>Давайте разберёмся.</h1><p>От первых двух полосок до сумки в роддом. Понятные объяснения, полезные списки и вопросы, которые стоит задать врачу.</p></section><div class="filter-panel"><div class="search-row"><label><span class="sr-only">Найти статью</span><input id="article-search" type="search" placeholder="Например: скрининг, сон, 20 неделя" autocomplete="off"></label><output id="result-count" aria-live="polite">Материалов: {len(arts)}</output></div><div class="filters" role="group" aria-label="Темы статей">{filters}</div></div><noscript><p>Все статьи доступны ниже. Для поиска на странице используйте поиск браузера.</p></noscript><div class="story-grid" id="articles">{''.join(card(a,True) for a in ordered)}</div><div class="empty" id="no-results" hidden><h2>Такой статьи пока нет</h2><p>Попробуйте другое слово или выберите все темы.</p><button class="filter" id="reset-search">Сбросить поиск</button></div></main>'''
    schema=[{'@context':'https://schema.org','@type':'CollectionPage','name':'Блог Маминой недельки','url':BASE+'/blog/index.html','hasPart':[{'@type':'Article','headline':a['title'],'url':BASE+f'/blog/{a["slug"]}.html'} for a in arts]}]
    return shell('Блог о беременности: недели, самочувствие, подготовка к родам | Мамина неделька','Статьи о беременности с источниками: обследования, самочувствие, подготовка к родам и повседневные вопросы. Выберите свою тему.', '/blog/index.html',body,source='blog',page='blog',schema=schema,preview=preview)

def home(arts,preview):
    body=(ROOT/'templates/home.html').read_text()
    by_slug={a['slug']:a for a in arts}
    body=body.replace('{{FEATURED}}',''.join(card(by_slug[s]) for s in ['polozhitelnyy-test','rodom','trevoga'] if s in by_slug))
    body=body.replace('{{WEEKS}}',''.join(f'<a href="/blog/{a["slug"]}.html" aria-label="{a["week"]} неделя беременности">{a["week"]}</a>' for a in sorted(arts,key=lambda a:a['week']) if a['category']=='weeks'))
    body=re.sub(r'\{\{BOT:([^|]+)\|([^}]+)\}\}',lambda m:bot_link('landing',m[1],m[2]),body)
    return shell('Мамина неделька — беременность по неделям и помощник в Telegram','Полезные статьи о беременности и приложение в Telegram: материалы по сроку, дневник самочувствия и вопросы к врачу. Начните с бесплатного доступа.','/',body,preview=preview)

def sitemap(arts, *, blog_only=False):
    ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9')
    root=ET.Element('{http://www.sitemaps.org/schemas/sitemap/0.9}urlset')
    paths=[('/',UPDATED),('/blog/index.html',UPDATED),('/about.html',UPDATED),('/editorial.html',UPDATED),('/privacy.html',UPDATED)]
    if blog_only: paths=[('/blog/index.html',UPDATED)]
    paths += [(f'/blog/{a["slug"]}.html',a['modified']) for a in arts]
    for path,date in paths:
        url=ET.SubElement(root,'url');ET.SubElement(url,'loc').text=BASE+path;ET.SubElement(url,'lastmod').text=PAGE_UPDATED.get(path,date)
    return '<?xml version="1.0" encoding="UTF-8"?>\n'+ET.tostring(root,encoding='unicode')+'\n'

def validate(arts,sources):
    if not arts: raise ValueError('No articles found')
    slugs={a['slug'] for a in arts}
    if len(slugs)!=len(arts): raise ValueError('Duplicate slugs')
    for a in arts:
        date.fromisoformat(a['modified'])
        if not a['title'] or not a['intro']: raise ValueError(f'{a["slug"]}: title and intro required')
        if not a['sources']: raise ValueError(f'{a["slug"]}: missing sources')
        for s in a['sources']:
            if s not in sources: raise ValueError(f'{a["slug"]}: unknown source {s}')
        for s in a['related']:
            if s not in slugs or s==a['slug']: raise ValueError(f'{a["slug"]}: invalid related {s}')
        if len(a['desc'])>180 or len(a['desc'])<55: raise ValueError(f'{a["slug"]}: description length')
        if a['status'] not in ('specialist_review','owner_review','approved'):raise ValueError('Unknown approval state')


def release_blockers(arts, config, *, public_preview=False, blog_release=False):
    """Report actual outstanding approvals; never infer them from build success."""
    gates = BLOG_RELEASE_GATES if blog_release else PUBLIC_PREVIEW_GATES if public_preview else RELEASE_GATES
    missing = [k for k in gates if config.get(k) is not True]
    if not public_preview and not blog_release:
        missing += [a['id'] for a in arts if a['status'] != 'approved' or not a['review_evidence'].strip()]
    return missing


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',nargs='?',type=Path,default=SOURCE)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--release',action='store_true')
    modes.add_argument('--public-preview',action='store_true',help='Authorized public version, with noindex and review notices')
    modes.add_argument('--blog-release',action='store_true',help='Owner-authorized blog indexing; preserves pending reviews and non-blog noindex')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    sources=json.loads((args.source/'sources.json').read_text())
    arts=[parse(p) for p in sorted(args.source.glob('A-*.md'))];validate(arts,sources)
    deployment = args.release or args.public_preview or args.blog_release
    if deployment:
        config=json.loads((ROOT/'release-checklist.json').read_text())
        missing=release_blockers(arts, config, public_preview=args.public_preview, blog_release=args.blog_release)
        if missing: raise SystemExit(('Release' if args.release else 'Public preview')+' blocked: '+', '.join(missing))
        if not args.output or args.output.resolve()==ROOT: raise SystemExit('Deployment build requires a separate --output directory')
    out=(args.output or ROOT).resolve()
    if out in ROOT.parents: raise SystemExit('Output cannot be a parent of the repository')
    if deployment and out.exists() and any(out.iterdir()):
        raise SystemExit('Deployment output must be empty to avoid stale public files')
    out.mkdir(parents=True,exist_ok=True);(out/'blog').mkdir(exist_ok=True)
    if out!=ROOT:
        (out/'assets').mkdir(exist_ok=True)
        for name in ('site.css','site.js'): shutil.copy2(ROOT/'assets'/name,out/'assets'/name)
        shutil.copytree(ROOT/'assets/illustrations',out/'assets/illustrations',dirs_exist_ok=True)
        shutil.copytree(ROOT/'blog/assets',out/'blog/assets',dirs_exist_ok=True)
    preview = 'blog-release' if args.blog_release else 'public-preview' if args.public_preview else not args.release
    for a in arts:(out/'blog'/f'{a["slug"]}.html').write_text(article(a,arts,sources,preview),encoding='utf-8')
    (out/'blog/index.html').write_text(catalogue(arts,preview),encoding='utf-8')
    (out/'index.html').write_text(home(arts,preview),encoding='utf-8')
    for page,title,desc in [('about','О проекте и контакты','Кто делает Мамину недельку, как связаться с владельцем и получить поддержку.'),('editorial','Как мы готовим статьи','Редакционные принципы Маминой недельки: источники, исправления и границы медицинской информации.'),('privacy','Конфиденциальность','Какие данные используются на сайте Маминой недельки и что происходит при переходе в Telegram.')]:
        body=(ROOT/f'templates/{page}.html').read_text()
        (out/f'{page}.html').write_text(shell(title+' | Мамина неделька',desc,f'/{page}.html',body,page=page,preview=preview),encoding='utf-8')
    (out/'404.html').write_text(shell('Страница не найдена | Мамина неделька','Вернитесь к полезным статьям о беременности или на главную страницу.','/404.html','<main class="wrap legal" id="main"><div class="eyebrow">404</div><h1>Эта страница не нашлась</h1><p>Возможно, в адресе опечатка. Найдите нужную тему в блоге.</p><a class="btn" href="/blog/index.html">Перейти в блог</a></main>',page='404',preview=preview or True),encoding='utf-8')
    (out/'sitemap.xml').write_text(sitemap(arts,blog_only=args.blog_release),encoding='utf-8')
    (out/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /tg/\nDisallow: /yookassa/\nDisallow: /health\nSitemap: '+BASE+'/sitemap.xml\n',encoding='utf-8')
    manifest={'mode':'blog-release' if args.blog_release else 'release' if args.release else 'public-preview' if args.public_preview else 'preview','articles':len(arts),'sources':len(sources),'updated':UPDATED,'paths':[f'/blog/{a["slug"]}.html' for a in arts]}
    (out/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(arts)} articles; {manifest["mode"]} → {out}')

if __name__=='__main__': main()
