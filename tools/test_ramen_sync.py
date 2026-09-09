import copy, importlib.util, json, pathlib, tempfile, unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('sync',pathlib.Path(__file__).with_name('ramen_sync.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SITE=pathlib.Path(__file__).resolve().parents[1]/'ramen-tech-2026'
class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((SITE/'catalog.js').read_text().split('=',1)[1].strip().rstrip(';'))
        self.r=dict(key='test/fixture',slug='fixture',title='テスト交流会',dates=['2026-10-08'],start='10:00',end='11:00',location='Garraway F',url='https://example.com/event',tags=[],free=False,active=True,ticket='',description='')
    def refresh(self,c=None,feeds=None):
        return m.update_catalog(c or self.c,feeds if feeds is not None else {'members':[self.r]},'2026-09-10T06:00:00+09:00')[0]
    def test_jst_date_not_utc_display_field(self):
        r=m.member_record(dict(self.r,name='テスト',client='test',date='2026-10-07',eventStartDate='2026-10-08',eventEndDate='2026-10-08'))
        self.assertEqual(r['dates'],['2026-10-08'])
    def test_placeholder_time_is_unknown(self):self.assertEqual(m.times('00:00','23:59'),(None,None))
    def test_html_format_failure_does_not_execute_javascript(self):
        with self.assertRaises(ValueError):m.parse_members('<html>login required</html>')
    def test_malicious_url_rejected(self):self.assertEqual(m.safe_url('javascript:alert(1)'),'')
    def test_real_title_angle_brackets_preserved(self):self.assertIn('<Day2>',m.clean('MAP <Day2>'))
    def test_new_event_added_and_stable(self):
        a=self.refresh();b=self.refresh(a)
        self.assertEqual(len(a['events']),len(self.c['events'])+1);self.assertEqual(len(a['events']),len(b['events']))
    def test_manual_events_unchanged(self):
        a=self.refresh()
        for ident in m.MANUAL:
            old=next(e for e in self.c['events'] if e['id']==ident);new=next(e for e in a['events'] if e['id']==ident)
            for k,v in old.items():self.assertEqual(v,new[k],ident)
    def test_changed_start_time_applied(self):
        a=self.refresh();self.r['start']='10:30';b=self.refresh(a)
        e=next(e for e in b['events'] if e['title']=='テスト交流会');self.assertEqual(e['start'],'10:30')
    def test_explicit_cancellation_blocks_calendar(self):
        self.r['title']='テスト交流会【中止】';a=self.refresh();e=next(e for e in a['events'] if e['title']==self.r['title'])
        self.assertEqual(e['status'],'cancelled');self.assertTrue(e['calendarBlocked'])
    def test_disappeared_event_retained_with_warning(self):
        a=self.refresh();b=self.refresh(a,{'members':[]})
        e=next(e for e in b['events'] if e['title']==self.r['title']);self.assertEqual(e['status'],'check');self.assertTrue(e['calendarBlocked'])
    def test_two_feed_time_conflict(self):
        s={**self.r,'key':'unit-schedule','end':'12:00','address':''}
        a=self.refresh(feeds={'members':[self.r],'schedule':{'records':[s],'venues':[]}})
        e=next(e for e in a['events'] if e['title']==self.r['title']);self.assertTrue(e['calendarBlocked'])
        s['end']='11:00';b=self.refresh(a,{'members':[self.r],'schedule':{'records':[s],'venues':[]}})
        e=next(e for e in b['events'] if e['title']==self.r['title']);self.assertFalse(e.get('calendarBlocked',False))
    def test_partial_run_does_not_clear_existing_conflict(self):
        s={**self.r,'key':'unit-schedule','end':'12:00','address':''}
        a=self.refresh(feeds={'members':[self.r],'schedule':{'records':[s],'venues':[]}})
        b=self.refresh(a,{'members':[self.r]});e=next(e for e in b['events'] if e['title']==self.r['title']);self.assertTrue(e['calendarBlocked'])
    def test_unknown_new_facility_keeps_address(self):
        s={**self.r,'key':'new-venue-slot','title':'会場追加テスト','location':'新しい会場','address':'福岡市中央区天神1-1'}
        a=self.refresh(feeds={'schedule':{'records':[s],'venues':[]}})
        e=next(e for e in a['events'] if e['title']==s['title']);v=next(v for v in a['venues'] if v['id']==e['venue']);self.assertEqual(v['address'],s['address'])
    def test_total_network_failure_keeps_catalog_and_last_success(self):
        with tempfile.TemporaryDirectory() as temp:
            p=pathlib.Path(temp);raw=(SITE/'catalog.js').read_bytes();(p/'catalog.js').write_bytes(raw)
            (p/'index.html').write_text('<head></head>');(p/'app.js').write_text('')
            oldtime='2026-09-09T06:00:00+09:00';(p/'sync-status.json').write_text(json.dumps({'lastSuccessAt':oldtime}))
            with patch.object(m,'get_text',side_effect=OSError('offline')),patch('sys.argv',['sync','--site',temp]):m.main()
            self.assertEqual(raw,(p/'catalog.js').read_bytes());r=json.loads((p/'sync-status.json').read_text());self.assertEqual(r['status'],'failed');self.assertEqual(r['lastSuccessAt'],oldtime)
if __name__=='__main__':unittest.main()
