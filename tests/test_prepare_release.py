import unittest
from pathlib import Path
from scripts.prepare_indexed_release import candidate_config


class SubsequentBlogRelease(unittest.TestCase):
    def test_updating_indexed_blog_preserves_header_scope_without_duplicates(self):
        before = ('root * /srv/old\n'
                  '@mamina_nonindexed not path /blog/*.html\n'
                  'header @mamina_nonindexed X-Robots-Tag "noindex, follow"\n')
        after = candidate_config(before, Path('/srv/old'), Path('/srv/new'), 'blog-release')
        self.assertEqual(after, before.replace('/srv/old', '/srv/new'))

    def test_full_release_removes_only_the_known_blog_header_pair(self):
        before = ('root * /srv/old\n'
                  '@mamina_nonindexed not path /blog/*.html\n'
                  'header @mamina_nonindexed X-Robots-Tag "noindex, follow"\n'
                  'header Cache-Control "no-cache"\n')
        after = candidate_config(before, Path('/srv/old'), Path('/srv/new'), 'release')
        self.assertEqual(after, 'root * /srv/new\nheader Cache-Control "no-cache"\n')


if __name__ == '__main__':
    unittest.main()
