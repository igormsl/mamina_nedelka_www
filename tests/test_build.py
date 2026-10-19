import copy
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import build_blog as b

class BuildContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.arts=[b.parse(p) for p in sorted(b.SOURCE.glob('A-*.md'))]
        cls.sources=json.loads((b.SOURCE/'sources.json').read_text())
    def test_raw_html_and_unsafe_links_are_not_executable(self):
        out=b.inline('<img src=x onerror=alert(1)> [x](javascript:alert) [ok](/blog/rodom.html)')
        self.assertNotIn('<img',out);self.assertNotIn('href="javascript:',out);self.assertIn('href="/blog/rodom.html"',out)
    def test_unknown_reference_is_rejected(self):
        arts=copy.deepcopy(self.arts);arts[0]['sources']=['does-not-exist']
        with self.assertRaisesRegex(ValueError,'unknown source'):b.validate(arts,self.sources)
    def test_missing_related_article_is_rejected(self):
        arts=copy.deepcopy(self.arts);arts[0]['related']=['does-not-exist']
        with self.assertRaisesRegex(ValueError,'invalid related'):b.validate(arts,self.sources)
    def test_modified_date_comes_from_source(self):
        a=copy.deepcopy(self.arts[0]);a['modified']='2026-09-01'
        html=b.article(a,[a]+self.arts[1:],self.sources,True)
        self.assertIn('"dateModified": "2026-09-01"',html)
        self.assertNotIn('datePublished',html)
    def test_pending_review_blocks_release_before_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'public'
            r=subprocess.run([sys.executable,str(b.ROOT/'build_blog.py'),'--release','--output',str(out)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('Release blocked',r.stderr);self.assertFalse(out.exists())
    def test_rebuild_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths=[]
            for i in (1,2):
                out=Path(tmp)/str(i)
                subprocess.run([sys.executable,str(b.ROOT/'build_blog.py'),'--output',str(out)],check=True,capture_output=True)
                paths.append({p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()})
            self.assertEqual(paths[0],paths[1])
    def test_public_preview_keeps_pending_reviews_and_noindex(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'public'
            subprocess.run([sys.executable,str(b.ROOT/'build_blog.py'),'--public-preview','--output',str(out)],check=True,capture_output=True)
            for path in out.rglob('*.html'):
                self.assertIn('content="noindex, follow"',path.read_text())
                self.assertNotIn('Локальный просмотр',path.read_text())
            article=next(a for a in self.arts if a['medical'])
            self.assertIn('Медицинская рецензия пока не проводилась',(out/'blog'/f'{article["slug"]}.html').read_text())
            self.assertEqual(json.loads((out/'build-manifest.json').read_text())['mode'],'public-preview')
    def test_public_preview_requires_its_own_authorization(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);script=root/'build_blog.py'
            shutil.copyfile(b.ROOT/'build_blog.py',script)
            (root/'release-checklist.json').write_text('{}')
            out=root/'public'
            r=subprocess.run([sys.executable,str(script),str(b.SOURCE),'--public-preview','--output',str(out)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('Public preview blocked',r.stderr);self.assertFalse(out.exists())
    def test_blog_release_indexes_only_blog_and_keeps_review_truth(self):
        from xml.etree import ElementTree as ET
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in b.SOURCE.glob('A-*.md')}
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'public'
            subprocess.run([sys.executable,str(b.ROOT/'build_blog.py'),'--blog-release','--output',str(out)],check=True,capture_output=True)
            for path in out.rglob('*.html'):
                indexed=b.blog_indexable('/'+path.relative_to(out).as_posix())
                self.assertEqual('content="noindex, follow"' in path.read_text(),not indexed)
                self.assertNotIn('Локальный просмотр',path.read_text())
            urls={e.text for e in ET.parse(out/'sitemap.xml').iter() if e.tag.endswith('loc')}
            self.assertEqual(len(urls),len(self.arts)+1)
            self.assertTrue(all(u.startswith(b.BASE+'/blog/') for u in urls))
            article=next(a for a in self.arts if a['medical'])
            self.assertIn('Медицинская рецензия пока не проводилась',(out/'blog'/f'{article["slug"]}.html').read_text())
            self.assertEqual(json.loads((out/'build-manifest.json').read_text())['mode'],'blog-release')
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in b.SOURCE.glob('A-*.md')})

    def test_blog_release_requires_its_explicit_authorization(self):
        config=dict.fromkeys(b.PUBLIC_PREVIEW_GATES+('owner_details_confirmed',),True)
        self.assertEqual(b.release_blockers(self.arts,config,blog_release=True),['blog_indexing_approved'])
    def test_site_validator_rejects_lost_google_ownership_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'public'
            subprocess.run([sys.executable,str(b.ROOT/'build_blog.py'),'--public-preview','--output',str(out)],check=True,capture_output=True)
            home=out/'index.html'
            home.write_text(home.read_text().replace(f'<meta name="google-site-verification" content="{b.GOOGLE_SITE_VERIFICATION}">',''))
            result=subprocess.run([sys.executable,str(b.ROOT/'scripts/check_site.py'),'--root',str(out),'--mode','public-preview'],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Google verification lost',result.stdout)
    def test_deployment_does_not_mix_with_stale_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);marker=out/'private.txt';marker.write_text('keep')
            r=subprocess.run([sys.executable,str(b.ROOT/'build_blog.py'),'--public-preview','--output',str(out)],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('must be empty',r.stderr)
            self.assertEqual(list(out.iterdir()),[marker]);self.assertEqual(marker.read_text(),'keep')
if __name__=='__main__':unittest.main()
