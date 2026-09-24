import copy, json, pathlib, unittest
from ramen_reconcile import reconcile_local, LOCAL_LINKS

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        path=pathlib.Path(__file__).resolve().parents[1]/'ramen-tech-2026/catalog.js'
        self.catalog=json.loads(path.read_text().split('=',1)[1].strip().rstrip(';'))
    def test_updates_times_keeps_saved_ids_and_local_notes(self):
        events={e['id']:e for e in self.catalog['events']}
        old_ids=set(events);notes=copy.deepcopy(events['welcome-7']['notes'])
        events[LOCAL_LINKS['coffee-7'][0]]['start']='10:15'
        reconcile_local(self.catalog)
        self.assertEqual(old_ids,{e['id'] for e in self.catalog['events']})
        self.assertEqual(events['coffee-7']['start'],'10:15')
        self.assertEqual(events['slot-f7ecd6ad-9115-45e5-8149-f6fdd21f5a92']['start'],'10:15')
        self.assertEqual(events['welcome-7']['notes'],notes)
        visible=[e for e in self.catalog['events'] if not e.get('duplicateOf') and e['venue']=='garraway' and e['dates']==['2026-10-07'] and 'COFFEE' in e['title']]
        self.assertEqual(len(visible),1)
    def test_cancellation_propagates_to_saved_aliases(self):
        events={e['id']:e for e in self.catalog['events']}
        official=events[LOCAL_LINKS['connect-8'][0]]
        official.update(status='cancelled',calendarBlocked=True)
        reconcile_local(self.catalog)
        for ident in ['connect-8',*LOCAL_LINKS['connect-8']]:
            self.assertEqual(events[ident]['status'],'cancelled')
            self.assertTrue(events[ident]['calendarBlocked'])
    def test_unrelated_similar_titles_not_merged(self):
        other=copy.deepcopy(self.catalog['events'][0]);other.update(id='unrelated-event',title='GENKI COFFEE MEETUP')
        self.catalog['events'].append(other);reconcile_local(self.catalog)
        self.assertNotIn('duplicateOf',other)

if __name__=='__main__':unittest.main()
