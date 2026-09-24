import copy
import json
from pathlib import Path
import unittest

from ramen_reviews import apply_time_reviews, correct_source_links, REVIEW_FILE
from ramen_reconcile import reconcile_local
from ramen_sync import update_catalog


class TimingReviewTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((REVIEW_FILE.parents[1] / 'catalog.json').read_text())
        self.reviews = json.loads(REVIEW_FILE.read_text())['reviews']
        self.now = '2026-09-25T06:00:00+09:00'
        # The live snapshot changes daily; arrange the exact reviewed state explicitly.
        for review in self.reviews:
            for event in self.catalog['events']:
                if event['id'] == review['eventId'] or event.get('duplicateOf') == review['eventId']:
                    event['dates'] = copy.deepcopy(review['dates'])
                    event['status'] = 'check'
                    event['calendarBlocked'] = True
                    event['notes'] = ['[自動確認] 時刻表記が不一致：登録と時間割。'] + review.get('supersededNotes', [])
                    event['sync']['hashes'] = copy.deepcopy(review['acceptedHashes'])
                    event['sync']['manualBlock'] = False
                    event['sync']['needsEditorialReview'] = False

    def apply(self):
        apply_time_reviews(self.catalog, self.now, self.reviews)
        reconcile_local(self.catalog)
        return {e['id']: e for e in self.catalog['events']}

    def test_padel_one_time_for_all_saved_ids(self):
        events = self.apply()
        for ident in ['event-auto-6d7aca132617f6', 'slot-members-founders-padel']:
            self.assertEqual((events[ident]['start'], events[ident]['end']), ('10:00', '12:00'))
            self.assertFalse(events[ident].get('calendarBlocked', False))
        snapshot = copy.deepcopy(self.catalog)
        self.apply()
        self.assertEqual(self.catalog, snapshot)

    def test_changed_upstream_data_requires_another_review(self):
        self.apply()
        event = next(e for e in self.catalog['events'] if e['id'] == self.reviews[0]['eventId'])
        event['sync']['hashes'][next(iter(self.reviews[0]['acceptedHashes']))] = 'changed'
        self.apply()
        self.assertTrue(event['calendarBlocked'])
        self.assertEqual(event['timeReview']['status'], 'needs-review')
        self.assertFalse(any(n.startswith('[主催者確認]') for n in event['notes']))

    def test_additional_source_is_not_silently_accepted(self):
        event = next(e for e in self.catalog['events'] if e['id'] == self.reviews[0]['eventId'])
        event['sync']['hashes']['schedule:new-entry'] = 'unreviewed'
        self.apply()
        self.assertTrue(event['calendarBlocked'])
        self.assertEqual(event['timeReview']['status'], 'needs-review')

    def test_cancellation_and_missing_sources_stay_blocked(self):
        for status, note in [('cancelled', '[自動確認] 公開情報に中止の記載があります。'),
                             ('check', '[自動確認] 公式登録の最新一覧に見当たりません。')]:
            with self.subTest(status=status):
                self.setUp()
                event = next(e for e in self.catalog['events'] if e['id'] == self.reviews[0]['eventId'])
                event.update(status=status, calendarBlocked=True)
                event['notes'].append(note)
                self.apply()
                self.assertEqual(event['status'], status)
                self.assertTrue(event['calendarBlocked'])

    def test_afterparty_detached_from_main_event_on_future_sync(self):
        key = 'ad088c2d-1bbb-434d-bd0e-4e4b29d12dca'
        main_id = 'event-design-boost-in-ramen-tech-2026-wha'
        party_id = 'event-auto-24c4d721f75f66'
        before = {e['id']: e for e in self.catalog['events']}
        before[main_id]['sync']['scheduleKeys'] = [key]
        before[party_id]['sync']['scheduleKeys'] = []
        corrected = correct_source_links(self.catalog)
        events = {e['id']: e for e in corrected['events']}
        self.assertNotIn(key, events[main_id]['sync']['scheduleKeys'])
        self.assertIn(key, events[party_id]['sync']['scheduleKeys'])
        record = dict(key=key, title=events[party_id]['title'], dates=['2026-10-08'],
                      start='21:00', end='23:00', location=events[party_id]['sync']['memberLocation'],
                      address='', url=events[party_id]['url'], tags=[])
        updated, _ = update_catalog(corrected, {'schedule': {'records': [record], 'venues': []}}, self.now)
        result = {e['id']: e for e in updated['events']}
        self.assertEqual(result[main_id]['start'], '18:00')
        self.assertEqual(result[party_id]['start'], '21:00')
        self.assertNotIn(key, result[main_id]['sync']['scheduleKeys'])
        self.assertIn(key, result[party_id]['sync']['scheduleKeys'])


if __name__ == '__main__':
    unittest.main()
