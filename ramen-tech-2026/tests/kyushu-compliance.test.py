"""Static regression tests for the Kyushu feature's asset provenance and citations."""
import json
import hashlib
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / 'kyushu'


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class ComplianceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.events = json.loads((FEATURE / 'events.json').read_text())
        cls.manifest = json.loads((FEATURE / 'image-manifest.json').read_text())
        cls.page = (FEATURE / 'index.html').read_text()
        cls.dom = Elements()
        cls.dom.feed(cls.page)

    def test_event_dates_and_ids_preserved(self):
        expected = {'nagasaki-kunchi','afaf','sunset','mct','andsake','creators','toumyou','faf','fan','sicf','hakozaki','synapse','tour','saga-sake','taketa','sagafes','oktober','waguri','amakusa'}
        self.assertEqual({e['id'] for e in self.events}, expected)
        self.assertEqual(len(self.events), 19)
        for e in self.events:
            self.assertLessEqual(e['start'], '2026-10-21')
            self.assertGreaterEqual(e['end'], '2026-09-21')
            self.assertEqual(e['checked'], '2026-09-11')

    def test_only_original_generated_assets_shipped(self):
        allowed = {a['path'] for a in self.manifest['assets']}
        self.assertEqual(len(allowed), 19)
        self.assertEqual(len({e['image']['url'] for e in self.events}), 19)
        self.assertEqual(len({a['sha256'] for a in self.manifest['assets']}), 19)
        by_id = {e['id']: e for e in self.events}
        for asset in self.manifest['assets']:
            self.assertEqual(asset['eventIds'], [asset['id']])
            self.assertEqual(asset['path'], by_id[asset['id']]['image']['url'])
            self.assertEqual(asset['style'], 'oil-painting')
            self.assertEqual(hashlib.sha256((FEATURE / asset['path']).read_bytes()).hexdigest(), asset['sha256'])
        self.assertEqual(self.manifest['sourceImages'], [])
        self.assertEqual({str(p.relative_to(FEATURE)) for p in (FEATURE / 'images').iterdir() if p.is_file()}, allowed)
        for e in self.events:
            im = e['image']
            self.assertEqual(im['kind'], 'ai-generated')
            self.assertIs(im['sourceImagesUsed'], False)
            self.assertEqual(im['style'], 'oil-painting')
            self.assertIn(im['url'], allowed)
            self.assertIn('AI生成', im['label'])
            self.assertIn('油絵風イメージ', im['alt'])
            self.assertNotIn('source', im)
            self.assertNotIn('originalUrl', im)
        for old in self.manifest['removedExternalPhotoFiles'] + self.manifest['retiredGeneratedFiles']:
            self.assertFalse((FEATURE / 'images' / old).exists())

    def test_images_are_local_and_declared_generated(self):
        images = [attrs for tag,attrs in self.dom.items if tag == 'img']
        self.assertEqual(len(images), 22)
        for im in images:
            self.assertTrue(im['src'].startswith('images/ai-'))
            self.assertIn('油絵風イメージ', im['alt'])
            self.assertTrue((FEATURE / im['src']).is_file())
        self.assertNotIn('class="cover-image-tag"', self.page)
        self.assertNotIn('class="photo-tag"', self.page)
        self.assertEqual(self.page.count('id="image-policy"'), 1)
        self.assertEqual(self.page.count('実際のイベント写真ではありません。'), 1)
        self.assertLess(self.page.index('id="image-policy"'), self.page.index('class="cover"'))

    def test_sources_are_clear_and_not_false_endorsement(self):
        self.assertEqual(self.page.count('class="card-source"'), 19)
        self.assertEqual(self.page.count('class="source-publisher"'), 19)
        self.assertIn('class="reference-publisher"', self.page)
        self.assertIn('情報の掲載元は、画像の提供元ではありません', self.page)
        self.assertNotIn('テーマ別に共通使用', self.page)
        for e in self.events:
            self.assertTrue(e['source'].startswith('https://'))
            self.assertTrue(e['sourceName'])
            self.assertIn(e['sourceKind'], ['official','media','tourism'])
            if 'fukuoka-now.com' in e['source']:
                self.assertEqual(e['sourceKind'], 'media')
            self.assertIn(e['source'], self.page)
        self.assertIn('Fukuoka Now「福岡秋のガイド2026」', self.page)
        self.assertIn('参照先との提携・公認を示すものではありません', self.page)
        self.assertIn('画像の更新日は、イベント情報の再確認日ではありません', self.page)
        for tag,attrs in self.dom.items:
            if tag == 'a' and attrs.get('target') == '_blank':
                self.assertIn('noopener', attrs['rel'])
                self.assertIn('noreferrer', attrs['rel'])

    def test_dialog_and_entry_use_new_assets(self):
        js = (FEATURE / 'kyushu.js').read_text()
        entry = (ROOT / 'classic-ui.js').read_text()
        self.assertNotIn('class="image-disclosure"', js)
        self.assertNotIn('class="dialog-credit"', js)
        self.assertIn('aria-describedby="image-policy"', self.page)
        self.assertIn('class="dialog-sources"', js)
        self.assertNotIn('e.image.source', js)
        self.assertIn('images/ai-oil-nagasaki-kunchi-20260912.webp', entry)
        self.assertNotIn('kyushu-entry-image-label', entry)
        self.assertNotIn('images/nagasaki-kunchi.webp', entry)
        self.assertIn('20260912k4', self.page)
        embedded = re.search(r'<script type="application/json" id="event-data">(.*?)</script>', self.page, re.S)
        self.assertEqual(len(json.loads(embedded.group(1))), 19)


if __name__ == '__main__':
    unittest.main()
