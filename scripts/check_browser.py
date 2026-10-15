#!/usr/bin/env python3
"""Uses workspace Playwright; preview.py must already run. Never opens Telegram."""
import json
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent.parent
BASE='http://127.0.0.1:8765'
SHOTS=ROOT.parents[1]/'screenshots/mamina_www'
SHOTS.mkdir(parents=True,exist_ok=True)
paths=['/','/blog/index.html','/about.html','/editorial.html','/privacy.html']+json.loads((ROOT/'build-manifest.json').read_text())['paths']
errors=[];external=set();overflow=[];checks=[];sizes={};metrics={}
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(viewport={'width':1280,'height':900})
    page=context.new_page()
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('request',lambda r:external.add(r.url) if not r.url.startswith(BASE) else None)
    for w in [320,360,390,768,1024,1280,1440]:
        page.set_viewport_size({'width':w,'height':900})
        for path in paths:
            response=page.goto(BASE+path,wait_until='load');assert response.status==200,path
            over=page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
            if over:overflow.append([path,w])
        checks.append(f'{len(paths)} pages at {w}px')
    page.set_viewport_size({'width':390,'height':844});page.goto(BASE)
    toggle=page.locator('.menu-toggle');toggle.click();assert toggle.get_attribute('aria-expanded')=='true'
    page.keyboard.press('Escape');assert toggle.get_attribute('aria-expanded')=='false'
    toggle.click();page.locator('#navigation a').first.click();assert page.url.endswith('/blog/index.html')
    assert toggle.get_attribute('aria-expanded')=='false';checks.append('mobile menu + Escape + link')
    page.locator('#article-search').fill('20 неделя');assert page.locator('[data-article]:visible').count()==1
    page.locator('[data-filter="weeks"]').click();assert page.locator('[data-article]:visible').count()==1
    page.locator('[data-filter="feel"]').click();assert page.locator('#no-results').is_visible()
    page.locator('#reset-search').click();assert page.locator('[data-article]:visible').count()==50
    page.locator('#article-search').fill('отек');assert page.locator('[data-article]:visible').count()>=1
    checks.append('search, category intersection, zero state, reset, ё normalization')
    page.goto(BASE+'/blog/polozhitelnyy-test.html?utm_source=telegram')
    assert page.locator('[data-bot="article_end"]').get_attribute('href').endswith('blog_a0047_article_end_tg')
    page.evaluate('''window.addEventListener('mamina:bot-click',e=>window.lastBotEvent=e.detail);document.querySelector('[data-bot="article_end"]').addEventListener('click',e=>e.preventDefault());''')
    page.locator('[data-bot="article_end"]').click()
    assert page.evaluate('window.lastBotEvent.source')=='blog_a0047_article_end_tg'
    assert page.evaluate('window.lastBotEvent.placement')=='article_end'
    checks.append('CTA source, channel, local click event without network')
    page.goto(BASE+'/?utm_source=unknown');assert page.locator('[data-bot="hero"]').get_attribute('href').endswith('landing_hero')
    page.goto(BASE);page.locator('summary').first.click();assert page.locator('details').first.get_attribute('open') is not None
    page.emulate_media(reduced_motion='reduce');assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches');checks.append('FAQ + reduced motion')
    assert not context.cookies();assert page.evaluate('localStorage.length+sessionStorage.length')==0
    checks.append('no cookies/storage; no external subrequests')
    for width,kind in [(1440,'desktop'),(390,'mobile')]:
        page.set_viewport_size({'width':width,'height':900 if width>400 else 844})
        for name,path in [('home','/'),('blog','/blog/index.html'),('article','/blog/polozhitelnyy-test.html')]:
            page.goto(BASE+path)
            # Trigger native lazy loading throughout the full-page capture.
            height=page.evaluate('document.body.scrollHeight')
            for y in range(0,height,650):page.evaluate('(y)=>scrollTo(0,y)',y);page.wait_for_timeout(35)
            page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
            page.evaluate('scrollTo(0,0)');page.wait_for_timeout(100)
            page.screenshot(path=str(SHOTS/f'2026-10-15_{name}_{kind}.png'),full_page=True)
            page.screenshot(path=str(SHOTS/f'2026-10-15_{name}_{kind}_viewport.png'))
            metrics[f'{name}_{kind}']=page.evaluate('''()=>({requests:performance.getEntriesByType('resource').length,bytes:performance.getEntriesByType('resource').reduce((n,r)=>n+r.encodedBodySize,0),domReadyMs:performance.getEntriesByType('navigation')[0].domContentLoadedEventEnd})''')
    nojs=browser.new_context(java_script_enabled=False);np=nojs.new_page();np.goto(BASE+'/blog/index.html');assert np.locator('[data-article]:visible').count()==50;checks.append('all 50 articles reachable without JS')
    browser.close()
for path,expected in [('/does-not-exist',404),('/.git/config',404),('/docs/evidence/original-inventory.json',404),('/templates/home.html',404),('/health',404)]:
    try:status=urlopen(BASE+path).status
    except HTTPError as e:status=e.code
    assert status==expected,(path,status)
checks.append('real 404; repo files and bot endpoints not exposed by preview')
result={'checks':checks,'viewport_checks':len(paths)*7,'overflow':overflow,'js_errors':errors,'external_subrequests':sorted(external),'local_performance_not_field_CWV':metrics,'screenshots':str(SHOTS),'passed':not(errors or overflow or external)}
(ROOT/'docs/evidence/browser-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2));assert result['passed']
