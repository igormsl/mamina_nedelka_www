#!/usr/bin/env python3
"""Local preview only: serve public artifacts, never repository sources or .git."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
ROOT = Path(__file__).resolve().parent.parent

class Preview(SimpleHTTPRequestHandler):
    def allowed(self):
        path = unquote(urlsplit(self.path).path)
        target = (ROOT / path.lstrip('/')).resolve()
        if not target.is_relative_to(ROOT): return False
        rel = target.relative_to(ROOT)
        return (path in ('/', '/blog/') or
                len(rel.parts) == 1 and rel.name in ('index.html','about.html','editorial.html','privacy.html','404.html','robots.txt','sitemap.xml') or
                len(rel.parts) == 2 and rel.parts[0] == 'blog' and rel.suffix == '.html' or
                rel.parts[:1] == ('assets',) and rel.suffix in ('.css','.js','.svg','.png','.jpg','.webp') or
                rel.parts[:2] == ('blog','assets') and rel.suffix in ('.png','.jpg','.svg','.webp')) and not any(x.startswith('.') for x in rel.parts)

    def send_head(self):
        if not self.allowed():
            self.send_error(404); return None
        parsed = urlsplit(self.path)
        if parsed.path in ('/blog/','/index.html'):
            location = '/blog/index.html' if parsed.path == '/blog/' else '/'
            self.send_response(301); self.send_header('Location', location + ('?' + parsed.query if parsed.query else '')); self.end_headers(); return None
        return super().send_head()

    def send_error(self, code, message=None, explain=None):
        if code == 404 and (ROOT/'404.html').exists():
            data=(ROOT/'404.html').read_bytes()
            self.send_response(404); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.end_headers()
            if self.command != 'HEAD': self.wfile.write(data)
        else: super().send_error(code,message,explain)

    def list_directory(self, path):
        self.send_error(404); return None

    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Robots-Tag','noindex, nofollow')
        self.send_header('X-Content-Type-Options','nosniff')
        super().end_headers()

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    print(f'Local review: http://localhost:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),partial(Preview,directory=str(ROOT))).serve_forever()
