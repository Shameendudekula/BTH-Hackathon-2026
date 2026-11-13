import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from dynamic import refresh_due, visible_catalogue, RefreshJobs
from core import catalogue, Store
from extended import demo_records
import tempfile, os, threading

class DynamicTests(unittest.TestCase):
    def test_default_no_static(self):
        self.assertEqual(visible_catalogue([]),{})
        self.assertEqual(visible_catalogue(catalogue()+demo_records()),{})
    def test_explicit_offline(self):
        self.assertTrue(visible_catalogue([],snapshots=True))
        self.assertTrue(visible_catalogue([],simulated=True))
    def test_live_replaces_snapshot(self):
        old=catalogue()[0]; live={**old,'mode':'Live public extraction','title':'Updated'}
        self.assertEqual(visible_catalogue([live],True)[old['id']]['title'],'Updated')
    def test_refresh_ttl(self):
        now=datetime.now(timezone.utc)
        self.assertTrue(refresh_due({}))
        self.assertFalse(refresh_due({'time':now.isoformat()},clock=now))
        self.assertTrue(refresh_due({'time':(now-timedelta(hours=7)).isoformat()},clock=now))
    def test_job_deduplication(self):
        with tempfile.TemporaryDirectory() as d:
            path=os.path.join(d,'db.sqlite3'); s=Store(path); w=s.new_workspace(); gate=threading.Event(); jobs=RefreshJobs(1)
            def fake(*args): gate.wait(2); return [],[]
            try:
                with patch('dynamic.refresh_all',side_effect=fake):
                    a=jobs.submit(path,w); b=jobs.submit(path,w); self.assertIs(a,b); gate.set(); self.assertEqual(a.result(timeout=3),([],[]))
            finally: gate.set(); jobs.pool.shutdown()
