#!/usr/bin/env python3
"""Prepare a frozen indexed-release operation after real approvals. Never apply it.

Creates a dated bundle outside Git/Mutagen. Until the source reviews and checklist
are complete it exits before creating files. Root activation is a separate step.
"""
import difflib
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import sys
import tarfile
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_blog as build

spec = importlib.util.spec_from_file_location('deploy_site', ROOT / 'scripts/deploy_site.py')
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def static_root(config):
    routes = [r for server in config['apps']['http']['servers'].values()
              for r in server.get('routes', [])
              if r.get('match') == [{'host': ['maminanedelka.ru']}]]
    if len(routes) != 1:
        raise RuntimeError('Expected one apex route')
    fallback = routes[0]['handle'][0]['routes'][-1]
    roots = []
    def visit(value):
        if isinstance(value, dict):
            if value.get('handler') == 'vars' and 'root' in value:
                roots.append(value['root'])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(fallback)
    if len(roots) != 1:
        raise RuntimeError('Expected one static root')
    return Path(roots[0])


def candidate_config(before, previous_root, target, mode='release'):
    old = 'root * ' + str(previous_root)
    if before.count(old) != 1:
        raise RuntimeError('Static root text is ambiguous')
    after = before.replace(old, 'root * ' + str(target))
    lines = after.splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines) if line.strip() == 'header X-Robots-Tag "noindex, follow"']
    scoped = [i for i, line in enumerate(lines) if line.strip() == 'header @mamina_nonindexed X-Robots-Tag "noindex, follow"']
    if len(matches) + len(scoped) != 1:
        raise RuntimeError('Expected exactly one known static indexing header; inspect the fallback')
    width = 1
    if scoped:
        i = scoped[0] - 1
        if i < 0 or lines[i].strip() != '@mamina_nonindexed not path /blog/*.html':
            raise RuntimeError('Unexpected indexing matcher; prepare a fresh scoped diff')
        width = 2
    else:
        i = matches[0]
    if mode == 'blog-release':
        indent = lines[i][:len(lines[i])-len(lines[i].lstrip())]
        lines[i:i+width] = [indent + '@mamina_nonindexed not path /blog/*.html\n' +
                           indent + 'header @mamina_nonindexed X-Robots-Tag "noindex, follow"\n']
    else:
        del lines[i:i+width]
    return ''.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('release', 'blog-release'), default='release')
    args = parser.parse_args()
    arts = [build.parse(p) for p in sorted(build.SOURCE.glob('A-*.md'))]
    build.validate(arts, json.loads((build.SOURCE / 'sources.json').read_text()))
    config = json.loads((ROOT / 'release-checklist.json').read_text())
    blockers = build.release_blockers(arts, config, blog_release=args.mode=='blog-release')
    if blockers:
        print(json.dumps({'state': 'blocked', 'blockers': blockers,
                          'production_changed': False, 'bundle_created': False}, ensure_ascii=False))
        return 2
    if socket.gethostname() != 'htogudjjkn':
        raise RuntimeError('Prepare on the documented target VPS after refreshing its baseline')
    before = deploy.CONFIG.read_text()
    adapted_before = deploy.adapted(deploy.CONFIG)
    previous_root = static_root(adapted_before)
    if previous_root.is_symlink() or previous_root.parent != deploy.RELEASES:
        raise RuntimeError('Unexpected live static root')
    old_files = deploy.inventory(previous_root)
    operation_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    bundle = Path.home() / '.local/state/mamina-www' / operation_id
    bundle.mkdir(parents=True, mode=0o700, exist_ok=False)
    backup = bundle / 'backup'
    backup.mkdir(mode=0o700)
    (backup / 'Caddyfile.before').write_text(before)
    (backup / 'Caddyfile.before').chmod(0o600)
    target = deploy.RELEASES / operation_id
    candidate = candidate_config(before, previous_root, target, args.mode)
    (bundle / 'Caddyfile.next').write_text(candidate)
    (bundle / 'Caddyfile.next').chmod(0o600)
    (bundle / 'Caddyfile.diff').write_text(''.join(difflib.unified_diff(
        before.splitlines(True), candidate.splitlines(True), fromfile='Caddyfile.before',
        tofile='Caddyfile.next', n=0)))
    if deploy.without_static(adapted_before) != deploy.without_static(deploy.adapted(bundle / 'Caddyfile.next')):
        raise RuntimeError('Candidate changes routes outside the static site')
    deploy.run('caddy', 'validate', '--config', str(bundle / 'Caddyfile.next'), '--adapter', 'caddyfile')
    deploy.run(sys.executable, '-B', str(ROOT / 'build_blog.py'), '--'+args.mode, '--output', str(bundle / 'public'))
    checks = deploy.run(sys.executable, '-B', str(ROOT / 'scripts/check_site.py'),
                        '--root', str(bundle / 'public'), '--mode', args.mode)
    (bundle / 'site-checks.json').write_text(checks)
    # This file is internal build metadata, never served publicly.
    (bundle / 'public/build-manifest.json').unlink()
    archive = backup / 'static-before.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(previous_root, arcname='site')
    with tempfile.TemporaryDirectory(prefix='mamina-restore-') as tmp:
        with tarfile.open(archive) as tar:
            tar.extractall(tmp, filter='data')
        if deploy.inventory(Path(tmp) / 'site') != old_files:
            raise RuntimeError('Static backup restore verification failed')
    units = ('caddy', 'mamina_bot', 'mamina_miniapp', 'mamina_support',
             'mamina_redirect', 'mamina-agent', 'mamina-dashboard')
    http_before = {u: deploy.response(u) for u in (
        deploy.DOMAIN + '/', deploy.DOMAIN + '/health',
        'http://127.0.0.1:8080/health', 'https://app.maminanedelka.ru/app/')}
    if any(r['status'] != 200 for r in http_before.values()):
        raise RuntimeError('An existing website/dependency is unavailable; do not activate')
    gates = build.BLOG_RELEASE_GATES if args.mode == 'blog-release' else build.RELEASE_GATES
    plan = {'id': operation_id, 'host': socket.gethostname(), 'mode': args.mode,
            'target': str(target), 'previous_root': str(previous_root), 'config': str(deploy.CONFIG),
            'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
            'candidate_sha256': deploy.sha(bundle / 'Caddyfile.next'),
            'static_archive_sha256': deploy.sha(archive), 'backup_restore_verified': True,
            'files': deploy.inventory(bundle / 'public'), 'old_files': old_files,
            'units': list(units), 'http_before': http_before,
            'release_approvals': {'gates': {k: config[k] for k in gates},
                'articles': {'blog/' + a['slug'] + '.html': {
                    'status': a['status'], 'review_evidence': a['review_evidence'],
                    'source_sha256': deploy.sha(build.SOURCE / a['file'])} for a in arts}}}
    (bundle / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    shutil.copy2(ROOT / 'scripts/deploy_site.py', bundle / 'deploy_site.py')
    deploy.check(bundle, plan)
    print(json.dumps({'state': 'prepared', 'bundle': str(bundle), 'production_changed': False,
                      'apply': f'sudo python3 {bundle}/deploy_site.py --bundle {bundle} --apply',
                      'rollback': f'sudo python3 {bundle}/deploy_site.py --bundle {bundle} --rollback'},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
