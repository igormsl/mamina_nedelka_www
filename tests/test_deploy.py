import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('deploy_site',Path(__file__).resolve().parents[1]/'scripts/deploy_site.py')
deploy=importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class RollbackContract(unittest.TestCase):
    def test_blog_deploy_accepts_pending_review_but_never_indexes_landing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);public=root/'public';(public/'blog').mkdir(parents=True)
            index='<meta name="robots" content="index, follow, max-image-preview:large">'
            noindex='<meta name="robots" content="noindex, follow">'
            (public/'index.html').write_text(noindex)
            (public/'blog/example.html').write_text(index)
            plan={'mode':'blog-release','files':{'index.html':'fixture','blog/example.html':'fixture'},
                  'release_approvals':{'gates':dict.fromkeys(deploy.BLOG_RELEASE_GATES,True),
                    'articles':{'blog/example.html':{'status':'specialist_review','review_evidence':''}}}}
            deploy.check_public_mode(root,plan)
            self.assertTrue(deploy.expected_header_noindex('assets/site.js','blog-release'))
            self.assertFalse(deploy.expected_header_noindex('blog/example.html','blog-release'))
            (public/'index.html').write_text(index)
            with self.assertRaisesRegex(RuntimeError,'indexing mode mismatch'):
                deploy.check_public_mode(root,plan)

    def test_release_refuses_unreviewed_articles_even_with_all_owner_gates(self):
        plan={'mode':'release','files':{'blog/example.html':'fixture'},
              'release_approvals':{'gates':dict.fromkeys(deploy.RELEASE_GATES,True),
                  'articles':{'blog/example.html':{'status':'specialist_review','review_evidence':''}}}}
        with self.assertRaisesRegex(RuntimeError,'missing article reviews'):
            deploy.check_public_mode(Path('/unused'),plan)

    def test_release_preserves_404_noindex_but_requires_other_html_indexable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);public=root/'public';(public/'blog').mkdir(parents=True)
            index='<meta name="robots" content="index, follow, max-image-preview:large">'
            noindex='<meta name="robots" content="noindex, follow">'
            (public/'index.html').write_text(index)
            (public/'blog/example.html').write_text(index)
            (public/'404.html').write_text(noindex)
            plan={'mode':'release','files':{p:'fixture' for p in ('index.html','blog/example.html','404.html')},
                  'release_approvals':{'gates':dict.fromkeys(deploy.RELEASE_GATES,True),
                      'articles':{'blog/example.html':{'status':'approved','review_evidence':'fixture-review'}}}}
            deploy.check_public_mode(root,plan)
            (public/'blog/example.html').write_text(noindex)
            with self.assertRaisesRegex(RuntimeError,'indexing mode mismatch'):
                deploy.check_public_mode(root,plan)

    def test_restores_exact_config_and_reloads_before_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'Caddyfile';backup=root/'backup';backup.mkdir()
            config.write_text('new configuration\n');config.chmod(0o640)
            before=backup/'Caddyfile.before';before.write_text('exact old configuration\n')
            plan={'candidate_sha256':deploy.sha(config),'before_sha256':deploy.sha(before)}
            events=[]
            def verify(plan,published):
                self.assertFalse(published)
                self.assertEqual(config.read_bytes(),before.read_bytes())
                self.assertEqual(events[-1],('systemctl','reload','caddy'))
                return {'restored':True}
            with patch.object(deploy,'CONFIG',config),patch.object(deploy,'run',side_effect=lambda *a:events.append(a)),patch.object(deploy,'verify',side_effect=verify):
                deploy.rollback(root,plan,backup)
            self.assertEqual(config.stat().st_mode & 0o777,0o640)
            self.assertIn('rolled_back',(root/'result.json').read_text())

    def test_rollback_does_not_overwrite_a_newer_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'Caddyfile';config.write_text('changed by another operator\n')
            with patch.object(deploy,'CONFIG',config),patch.object(deploy,'run') as run:
                with self.assertRaisesRegex(RuntimeError,'automatic rollback refused'):
                    deploy.rollback(root,{'candidate_sha256':'different'},root)
                run.assert_not_called()
            self.assertEqual(config.read_text(),'changed by another operator\n')

    def test_inventory_rejects_symlinks_to_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);public=root/'public';public.mkdir()
            secret=root/'private';secret.write_text('test fixture')
            (public/'leak').symlink_to(secret)
            with self.assertRaisesRegex(RuntimeError,'Symlink'):
                deploy.inventory(public)


if __name__=='__main__':unittest.main()
