#!/usr/bin/env python3
"""Read-only release/indexability audit. No cabinet credentials or server changes.

Run --live to inspect the public sitemap and every canonical page. Exit 2 means
the release is not ready, not a transport failure. Search index membership is
not inferred from a 200 response or from Search Console ownership.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_blog as build
from scripts.check_site import Page

MAX_BYTES = 2 * 1024 * 1024


def canonical_url(url):
    u = urlsplit(url)
    return (u.scheme == 'https' and u.netloc == 'maminanedelka.ru'
            and not u.query and not u.fragment and u.path.startswith('/'))


class SiteRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not canonical_url(newurl):
            raise ValueError('Redirect outside canonical site')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    if not canonical_url(url):
        raise ValueError('Only canonical Mamina URLs may be inspected')
    request = Request(url, headers={'User-Agent': 'MaminaSearchReadiness/1.0'})
    try:
        try:
            response = build_opener(SiteRedirects()).open(request, timeout=20)
        except HTTPError as error:
            response = error
        with response:
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError('Response exceeds audit size limit')
            info = {'url': url, 'final_url': response.geturl(), 'status': response.status,
                    'content_type': response.headers.get('Content-Type', ''),
                    'x_robots_tag': response.headers.get('X-Robots-Tag', ''),
                    'sha256': hashlib.sha256(body).hexdigest()}
            return info, body.decode('utf-8')
    except (OSError, URLError, ValueError, UnicodeError):
        # Do not echo arbitrary server error pages, query strings or credentials.
        return {'url': url, 'status': None, 'error': 'request_failed'}, ''


def inspect_page(url, robots):
    info, body = fetch(url)
    issues = []
    if info['status'] != 200:
        issues.append('http_not_200')
    if info.get('final_url') != url:
        issues.append('noncanonical_redirect')
    if 'text/html' not in info.get('content_type', ''):
        issues.append('not_html')
    try:
        page = Page(Path(urlsplit(url).path), text=body)
        info.update(meta_robots=page.meta.get('robots', ''), canonical=page.canonical,
                    title=page.title, h1=page.h1)
        if page.canonical != [url]:
            issues.append('canonical_mismatch')
        if not page.title or page.h1 != 1:
            issues.append('title_or_h1_missing')
        if 'noindex' in page.meta.get('robots', '').lower():
            issues.append('meta_noindex')
        if page.meta.get('yandex-verification') != '5de9122d74676c4f':
            issues.append('yandex_verification_missing')
        if url == build.BASE + '/':
            info['google_verification_present'] = page.meta.get('google-site-verification') == build.GOOGLE_SITE_VERIFICATION
            if not info['google_verification_present']:
                issues.append('google_verification_missing')
    except (ValueError, KeyError):
        issues.append('invalid_html_or_jsonld')
    if 'noindex' in info.get('x_robots_tag', '').lower():
        issues.append('header_noindex')
    if not robots.can_fetch('Googlebot', url) or not robots.can_fetch('YandexBot', url):
        issues.append('robots_disallow')
    info['issues'] = issues
    info['technically_indexable'] = not issues
    return info


def live_audit(arts, *, blog_only=False):
    sitemap_info, sitemap_text = fetch(build.BASE + '/sitemap.xml')
    robots_info, robots_text = fetch(build.BASE + '/robots.txt')
    errors = []
    if sitemap_info['status'] != 200 or robots_info['status'] != 200:
        errors.append('sitemap_or_robots_unavailable')
    try:
        entries = [e.text for e in ET.fromstring(sitemap_text).iter() if e.tag.endswith('loc')]
    except ET.ParseError:
        entries = []
        errors.append('invalid_sitemap')
    expected = {e.text for e in ET.fromstring(build.sitemap(arts,blog_only=blog_only)).iter() if e.tag.endswith('loc')}
    unique = set(entries)
    if len(unique) != len(entries):
        errors.append('duplicate_sitemap_urls')
    if unique != expected:
        errors.append('sitemap_source_mismatch')
    if any(not u or not canonical_url(u) for u in unique):
        errors.append('sitemap_has_noncanonical_url')
    urls = sorted(u for u in unique if u and canonical_url(u))
    robots = RobotFileParser()
    robots.parse(robots_text.splitlines())
    if not robots.site_maps() or build.BASE + '/sitemap.xml' not in robots.site_maps():
        errors.append('robots_sitemap_missing')
    with ThreadPoolExecutor(max_workers=5) as pool:
        pages = list(pool.map(lambda u: inspect_page(u, robots), urls))
    return {'sitemap': sitemap_info, 'robots': robots_info, 'errors': errors,
            'pages': pages, 'pages_checked': len(pages),
            'indexable_pages': sum(p['technically_indexable'] for p in pages),
            'issue_counts': dict(Counter(i for p in pages for i in p['issues'])),
            'index_membership': 'not_checked'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--mode', choices=('release','blog-release'), default='release')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    arts = [build.parse(p) for p in sorted(build.SOURCE.glob('A-*.md'))]
    build.validate(arts, json.loads((build.SOURCE / 'sources.json').read_text()))
    config = json.loads((ROOT / 'release-checklist.json').read_text())
    blockers = build.release_blockers(arts, config, blog_release=args.mode=='blog-release')
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'mode': args.mode, 'release_ready': not blockers, 'release_blockers': blockers,
              'gates': {k: config.get(k) is True for k in (build.BLOG_RELEASE_GATES if args.mode=='blog-release' else build.RELEASE_GATES)},
              'article_status_counts': dict(Counter(a['status'] for a in arts)),
              'articles': [{'file': a['file'], 'title': a['title'],
                            'url': build.BASE + '/blog/' + a['slug'] + '.html',
                            'medical': a['medical'], 'status': a['status'],
                            'review_evidence': a['review_evidence'], 'sources': a['sources'],
                            'sha256': hashlib.sha256((build.SOURCE / a['file']).read_bytes()).hexdigest()}
                           for a in arts]}
    if args.live:
        report['live'] = live_audit(arts,blog_only=args.mode=='blog-release')
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end='')
    live_ok = not args.live or (not report['live']['errors'] and
                               report['live']['indexable_pages'] == len(arts) + (1 if args.mode=='blog-release' else 5))
    return 0 if report['release_ready'] and live_ok else 2


if __name__ == '__main__':
    sys.exit(main())
