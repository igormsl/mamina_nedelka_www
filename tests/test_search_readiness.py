import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.robotparser import RobotFileParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_blog as build
from scripts import search_readiness as audit


class SearchReadiness(unittest.TestCase):
    def test_release_requires_review_evidence_even_with_all_owner_gates(self):
        arts = [build.parse(next(build.SOURCE.glob('A-*.md')))]
        config = dict.fromkeys(build.RELEASE_GATES, True)
        self.assertEqual(build.release_blockers(arts, config), [arts[0]['id']])
        reviewed = copy.deepcopy(arts)
        reviewed[0].update(status='approved', review_evidence='   ')
        self.assertEqual(build.release_blockers(reviewed, config), [arts[0]['id']])
        reviewed[0]['review_evidence'] = 'fixture-review-record'
        self.assertEqual(build.release_blockers(reviewed, config), [])

    def test_live_audit_cannot_fetch_foreign_or_credential_urls(self):
        for url in ('https://example.com/', 'https://user@maminanedelka.ru/',
                    'https://maminanedelka.ru/?secret=fixture', 'http://127.0.0.1/'):
            with self.assertRaisesRegex(ValueError, 'Only canonical'):
                audit.fetch(url)

    def test_200_and_index_meta_do_not_hide_header_noindex(self):
        robots = RobotFileParser()
        robots.parse(['User-agent: *', 'Allow: /'])
        body = build.shell('Title', 'Description', '/', '<h1>Test</h1>', preview=False)
        response = {'status': 200, 'final_url': build.BASE + '/',
                    'content_type': 'text/html', 'x_robots_tag': 'noindex, follow'}
        with patch.object(audit, 'fetch', return_value=(response, body)):
            result = audit.inspect_page(build.BASE + '/', robots)
        self.assertFalse(result['technically_indexable'])
        self.assertEqual(result['issues'], ['header_noindex'])

    def test_robots_block_still_fails_with_no_noindex_tags(self):
        robots = RobotFileParser()
        robots.parse(['User-agent: *', 'Disallow: /'])
        body = build.shell('Title', 'Description', '/', '<h1>Test</h1>', preview=False)
        response = {'status': 200, 'final_url': build.BASE + '/',
                    'content_type': 'text/html', 'x_robots_tag': ''}
        with patch.object(audit, 'fetch', return_value=(response, body)):
            result = audit.inspect_page(build.BASE + '/', robots)
        self.assertEqual(result['issues'], ['robots_disallow'])


if __name__ == '__main__':
    unittest.main()
