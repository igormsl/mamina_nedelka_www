#!/usr/bin/env python3
"""Apply one prepared Mamina static-site bundle. Default is read-only preflight.

Requires sudo only for --apply/--rollback. Keeps the old web root untouched.
Never changes bot services, databases or neighbouring virtual hosts.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.request

CONFIG = Path('/etc/caddy/Caddyfile')
RELEASES = Path('/srv/mamina-www-releases')
BACKUPS = Path('/var/backups/mamina-www')
DOMAIN = 'https://maminanedelka.ru'
RELEASE_GATES = ('owner_visual_acceptance', 'owner_details_confirmed',
                 'privacy_and_hosting_review', 'bot_telegram_smoke',
                 'vps_backup_and_rollback_plan', 'public_enable_approved')
BLOG_RELEASE_GATES = ('owner_visual_acceptance', 'owner_details_confirmed',
                      'vps_backup_and_rollback_plan', 'public_enable_approved', 'blog_indexing_approved')


def expected_header_noindex(name, mode):
    if mode == 'blog-release':
        return not bool(re.fullmatch(r'blog/[a-z0-9-]+\.html', name))
    return mode == 'public-preview'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('Symlink in deployment tree: ' + str(path))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha(path)
    return result


def run(*args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Command failed: ' + ' '.join(args) + '\n' + result.stderr[-1800:])
    return result.stdout


def adapted(path):
    return json.loads(run('caddy', 'adapt', '--config', str(path), '--adapter', 'caddyfile'))


def without_static(config):
    """Remove only the apex fallback; everything else must remain identical."""
    config = copy.deepcopy(config)
    found = 0
    for server in config['apps']['http']['servers'].values():
        for route in server.get('routes', []):
            if route.get('match') == [{'host': ['maminanedelka.ru']}]:
                routes = route['handle'][0]['routes']
                bot = [r for r in routes if r.get('match') == [{'path': ['/tg/*', '/yookassa/*', '/health']}]]
                if len(bot) != 1 or 'reverse_proxy' not in json.dumps(bot):
                    raise RuntimeError('Expected bot route is missing')
                fallback = routes[-1]
                if fallback.get('match') or fallback['handle'][0]['handler'] != 'subroute':
                    raise RuntimeError('Unexpected apex fallback structure')
                routes[-1] = {'static_site_placeholder': True}
                found += 1
    if found != 1:
        raise RuntimeError('Expected one apex virtual host')
    return config


def response(url):
    try:
        reply = urllib.request.urlopen(url, timeout=20)
    except urllib.error.HTTPError as error:
        reply = error
    with reply:
        body = reply.read()
        return {'status': reply.status, 'sha256': hashlib.sha256(body).hexdigest(),
                'bytes': len(body), 'noindex': 'noindex' in reply.headers.get('X-Robots-Tag', '')}


def check_public_mode(bundle, plan):
    mode = plan['mode']
    if mode not in ('public-preview', 'release', 'blog-release'):
        raise RuntimeError('Unknown public deployment mode')
    if mode in ('release', 'blog-release'):
        approvals = plan.get('release_approvals', {})
        gates = BLOG_RELEASE_GATES if mode == 'blog-release' else RELEASE_GATES
        if any(approvals.get('gates', {}).get(k) is not True for k in gates):
            raise RuntimeError('Indexed release is missing owner/operational approvals')
        reviews = approvals.get('articles', {})
        expected = {n for n in plan['files'] if n.startswith('blog/') and n.endswith('.html') and n != 'blog/index.html'}
        if not expected or set(reviews) != expected:
            raise RuntimeError('Indexed release review inventory mismatch')
        if mode == 'release' and any(r.get('status') != 'approved' or not str(r.get('review_evidence', '')).strip()
               for r in reviews.values()):
            raise RuntimeError('Indexed release is missing article reviews')
    for name in plan['files']:
        if name.endswith('.html'):
            text = (bundle / 'public' / name).read_text()
            expected_noindex = expected_header_noindex(name, mode) or name == '404.html'
            has_noindex = bool(re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', text))
            if has_noindex != expected_noindex:
                raise RuntimeError('HTML indexing mode mismatch: ' + name)
            if not expected_noindex and 'content="index, follow, max-image-preview:large"' not in text:
                raise RuntimeError('Indexed HTML must declare its mode: ' + name)


def check(bundle, plan):
    if not re.fullmatch(r'\d{8}T\d{6}Z', plan['id']):
        raise RuntimeError('Invalid deployment ID')
    if socket.gethostname() != plan['host'] or plan['host'] != 'htogudjjkn':
        raise RuntimeError('Wrong target host')
    if plan['target'] != str(RELEASES / plan['id']) or plan['config'] != str(CONFIG):
        raise RuntimeError('Unexpected production target')
    check_public_mode(bundle, plan)
    if plan.get('backup_restore_verified') is not True:
        raise RuntimeError('Backup restore was not verified')
    if sha(CONFIG) != plan['before_sha256']:
        raise RuntimeError('Caddyfile changed since baseline: prepare a fresh diff')
    if sha(bundle / 'backup/Caddyfile.before') != plan['before_sha256']:
        raise RuntimeError('Config backup differs from baseline')
    if sha(bundle / 'backup/static-before.tar.gz') != plan['static_archive_sha256']:
        raise RuntimeError('Static backup changed')
    if inventory(Path(plan['previous_root'])) != plan['old_files']:
        raise RuntimeError('Previous web root changed since backup')
    if sha(bundle / 'Caddyfile.next') != plan['candidate_sha256']:
        raise RuntimeError('Candidate configuration changed')
    if inventory(bundle / 'public') != plan['files']:
        raise RuntimeError('Public bundle changed or contains extra files')
    if 'index.html' not in plan['files']:
        raise RuntimeError('Homepage missing')
    before, after = adapted(CONFIG), adapted(bundle / 'Caddyfile.next')
    if without_static(before) != without_static(after):
        raise RuntimeError('Changes outside the static apex handler')
    with urllib.request.urlopen('http://127.0.0.1:2019/config/', timeout=5) as reply:
        if json.load(reply) != before:
            raise RuntimeError('Loaded Caddy config differs from disk')
    run('caddy', 'validate', '--config', str(bundle / 'Caddyfile.next'), '--adapter', 'caddyfile')
    for unit in plan['units']:
        if run('systemctl', 'is-active', unit).strip() != 'active':
            raise RuntimeError('Service is not active: ' + unit)
    for url, expected in plan['http_before'].items():
        actual = response(url)
        if actual['status'] != expected['status']:
            raise RuntimeError('HTTP baseline changed: ' + url)
    if Path(plan['target']).exists():
        raise RuntimeError('Release directory already exists; do not overwrite it')


def replace_config(source):
    old = CONFIG.stat()
    fd, name = tempfile.mkstemp(prefix='.mamina-', dir=CONFIG.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(source.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, old.st_mode & 0o777)
        os.chown(name, old.st_uid, old.st_gid)
        os.replace(name, CONFIG)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def verify(plan, published):
    checked = {}
    if published:
        for name, digest in plan['files'].items():
            url = DOMAIN + ('/' if name == 'index.html' else '/' + name)
            result = response(url)
            expected_noindex = expected_header_noindex(name, plan['mode'])
            if result['status'] != 200 or result['sha256'] != digest or result['noindex'] != expected_noindex:
                raise RuntimeError('Published file mismatch: ' + name)
            checked[url] = result
        for path in ('/not-a-real-mamina-page', '/.git/config', '/templates/home.html', '/docs/LEGAL.md', '/build-manifest.json'):
            result = response(DOMAIN + path)
            if result['status'] != 404:
                raise RuntimeError('Expected 404: ' + path)
    else:
        result = response(DOMAIN + '/')
        expected = plan['http_before'][DOMAIN + '/']
        if any(result[k] != expected[k] for k in ('status', 'sha256', 'noindex')):
            raise RuntimeError('Previous site status was not restored')
        checked[DOMAIN + '/'] = result
    for url in (DOMAIN + '/health', 'http://127.0.0.1:8080/health', 'https://app.maminanedelka.ru/app/'):
        result = response(url)
        if result['status'] != 200:
            raise RuntimeError('Dependency unavailable: ' + url)
        checked[url] = result
    if adapted(CONFIG) != json.load(urllib.request.urlopen('http://127.0.0.1:2019/config/', timeout=5)):
        raise RuntimeError('Loaded Caddy config differs after reload')
    for unit in plan['units']:
        if run('systemctl', 'is-active', unit).strip() != 'active':
            raise RuntimeError('Inactive service after reload: ' + unit)
    return checked


def receipt(bundle, state, **extra):
    path = bundle / 'result.json'
    path.write_text(json.dumps({'state': state, 'at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), **extra}, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o644)


def rollback(bundle, plan, backup):
    if sha(CONFIG) != plan['candidate_sha256']:
        raise RuntimeError('Current Caddyfile differs from this deployment; automatic rollback refused')
    if sha(backup / 'Caddyfile.before') != plan['before_sha256']:
        raise RuntimeError('Rollback configuration checksum mismatch')
    run('caddy', 'validate', '--config', str(backup / 'Caddyfile.before'), '--adapter', 'caddyfile')
    replace_config(backup / 'Caddyfile.before')
    run('systemctl', 'reload', 'caddy')
    checked = verify(plan, False)
    receipt(bundle, 'rolled_back', checks=checked)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--apply', action='store_true')
    action.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    bundle = args.bundle.resolve()
    plan = json.loads((bundle / 'plan.json').read_text())
    if args.apply or args.rollback:
        if os.geteuid() != 0:
            raise SystemExit('Run this prepared operation with sudo in the owner terminal')
        with open('/run/lock/mamina-www-deploy.lock', 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.rollback:
                backup = BACKUPS / plan['id']
                # Rollback trusts the root-owned record, not a later edited workspace plan.
                plan = json.loads((backup / 'plan.json').read_text())
                rollback(bundle, plan, backup)
                print('Previous Caddy configuration and HTTP state restored')
                return
            check(bundle, plan)
            backup = BACKUPS / plan['id']
            backup.mkdir(parents=True, mode=0o700, exist_ok=False)
            for name in ('Caddyfile.before', 'static-before.tar.gz'):
                shutil.copyfile(bundle / 'backup' / name, backup / name)
                (backup / name).chmod(0o600)
            for name in ('plan.json', 'Caddyfile.next'):
                shutil.copyfile(bundle / name, backup / name)
                (backup / name).chmod(0o600)
            target = Path(plan['target'])
            RELEASES.mkdir(mode=0o755, exist_ok=True)
            if RELEASES.is_symlink():
                raise RuntimeError('Release parent must not be a symlink')
            shutil.copytree(bundle / 'public', target)
            for path in [target, *target.rglob('*')]:
                path.chmod(0o755 if path.is_dir() else 0o644)
            if inventory(target) != plan['files']:
                raise RuntimeError('Installed static files differ from verified bundle')
            run('caddy', 'validate', '--config', str(backup / 'Caddyfile.next'), '--adapter', 'caddyfile')
            if sha(CONFIG) != plan['before_sha256']:
                raise RuntimeError('Caddy changed while copying files; activation aborted')
            replace_config(backup / 'Caddyfile.next')
            try:
                run('systemctl', 'reload', 'caddy')
                checked = verify(plan, True)
                receipt(bundle, 'deployed_' + plan['mode'].replace('-', '_'), target=str(target), checks=checked)
            except Exception:
                rollback(bundle, plan, backup)
                raise
            print('Published and verified: ' + DOMAIN + '/ (' + plan['mode'] + ')')
    else:
        check(bundle, plan)
        print('Preflight passed. No production changes made.')


if __name__ == '__main__':
    main()
