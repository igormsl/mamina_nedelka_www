#!/usr/bin/env python3
"""Offline integrity and SEO checks for the built site. No production requests."""
from html.parser import HTMLParser
import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, unquote, parse_qs
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
PROJECT=ROOT
sys.path.insert(0,str(ROOT))
import build_blog as build

class Page(HTMLParser):
    def __init__(self,path,text=None):
        super().__init__();self.path=path;self.ids=[];self.links=[];self.images=[];self.meta={};self.canonical=[];self.h1=0;self.title='';self.scripts=[];self.in_title=False;self.in_json=False;self.json_text='';self.bot=[]
        self.feed(path.read_text() if text is None else text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='h1':self.h1+=1
        if tag=='title':self.in_title=True
        if tag=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
        if tag=='a' and 'href' in a:
            self.links.append(a['href'])
            if 'data-bot' in a:self.bot.append(a['href'])
        if tag in ('img','script','link'):
            src=a.get('src') or (a.get('href') if a.get('rel') in ('stylesheet','icon') else None)
            if src:self.links.append(src)
        if tag=='img':self.images.append(a)
        if tag=='script' and a.get('type')=='application/ld+json':self.in_json=True;self.json_text=''
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
        if tag=='script' and self.in_json:self.scripts.append(json.loads(self.json_text));self.in_json=False
    def handle_data(self,data):
        if self.in_title:self.title+=data
        if self.in_json:self.json_text+=data

def main():
    global ROOT
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=PROJECT)
    parser.add_argument('--mode',choices=('preview','public-preview','release','blog-release'),default='preview')
    args=parser.parse_args()
    ROOT=args.root.resolve()
    arts=[build.parse(p) for p in sorted(build.SOURCE.glob('A-*.md'))]
    build.validate(arts,json.loads((build.SOURCE/'sources.json').read_text()))
    files=[ROOT/n for n in ['index.html','about.html','privacy.html','editorial.html','404.html']]+sorted((ROOT/'blog').glob('*.html'))
    pages={p.resolve():Page(p) for p in files};errors=[]
    def check(ok,msg):
        if not ok:errors.append(msg)
    if args.mode in ('release','blog-release'):
        blockers=build.release_blockers(arts,json.loads((PROJECT/'release-checklist.json').read_text()),blog_release=args.mode=='blog-release')
        check(not blockers,'release approvals missing: '+', '.join(blockers))
    titles=set();descs=set()
    for path,page in pages.items():
        rel=path.relative_to(ROOT).as_posix();prefix=rel+': '
        check(page.h1==1,prefix+'one h1 required')
        check(len(page.ids)==len(set(page.ids)),prefix+'duplicate IDs')
        check(page.title and page.title not in titles,prefix+'title absent/duplicate');titles.add(page.title)
        check(page.meta.get('description') and page.meta['description'] not in descs,prefix+'description absent/duplicate');descs.add(page.meta.get('description'))
        check(page.canonical==[build.BASE+('/' if rel=='index.html' else '/'+rel)],prefix+'canonical mismatch')
        check(page.meta.get('yandex-verification')=='5de9122d74676c4f',prefix+'Yandex verification lost')
        if rel=='index.html':
            check(page.meta.get('google-site-verification')==build.GOOGLE_SITE_VERIFICATION,prefix+'Google verification lost')
        noindex='noindex' in page.meta.get('robots','')
        expected_indexable = args.mode=='release' and rel!='404.html' or args.mode=='blog-release' and build.blog_indexable('/'+rel)
        check(noindex != expected_indexable,prefix+'indexing mode mismatch')
        if args.mode in ('public-preview','blog-release'):
            check('Локальный просмотр' not in path.read_text(),prefix+'local-only label on public preview')
        check(bool(page.scripts),prefix+'JSON-LD absent')
        og = page.meta.get('og:image','')
        check(og.startswith(build.BASE+'/') and (ROOT/og.removeprefix(build.BASE+'/')).is_file(),prefix+'OG image absent')
        for img in page.images:check(all(k in img for k in ('alt','width','height')),prefix+'image lacks alt or dimensions')
        for url in page.bot:
            u=urlsplit(url);start=parse_qs(u.query).get('start',[''])[0]
            check(u.netloc=='t.me' and u.path=='/mamina_nedelka_bot' and re.fullmatch('[a-z0-9_-]{1,64}',start),prefix+'invalid bot link')
        for link in page.links:
            u=urlsplit(build.site_href(link))
            if u.scheme or u.netloc:continue
            target=(ROOT/u.path.lstrip('/') if u.path.startswith('/') else path.parent/u.path) if u.path else path
            if target.is_dir():target=target/'index.html'
            target=target.resolve();check(target.is_file(),prefix+'missing '+link)
            if u.fragment and target in pages:check(unquote(u.fragment) in pages[target].ids,prefix+'missing anchor '+link)
    expected={build.BASE+'/blog/'+a['slug']+'.html' for a in arts}
    sitemap={e.text for e in ET.parse(ROOT/'sitemap.xml').iter() if e.tag.endswith('loc')}
    check(expected=={u for u in sitemap if '/blog/' in u and not u.endswith('/index.html')},'sitemap/source mismatch')
    expected_sitemap={e.text for e in ET.fromstring(build.sitemap(arts,blog_only=args.mode=='blog-release')).iter() if e.tag.endswith('loc')}
    check(sitemap==expected_sitemap,'sitemap scope mismatch')
    old=json.loads((PROJECT/'docs/evidence/original-inventory.json').read_text())
    oldslugs={x['slug'] for x in old} if isinstance(old,list) else set()
    check(oldslugs <= {a['slug'] for a in arts},'old URLs lost')
    check({p.stem for p in (ROOT/'blog').glob('*.html')}=={'index'}|{a['slug'] for a in arts},'stale/missing HTML article')
    print(json.dumps({'pages':len(pages),'articles':len(arts),'sitemap_urls':len(sitemap),'old_urls':len(oldslugs),'checks':'pass' if not errors else 'fail','errors':errors},ensure_ascii=False,indent=2))
    return bool(errors)

if __name__=='__main__':sys.exit(main())
