import os, tempfile, unittest
from unittest.mock import patch
from core import Store, rank, catalogue, baseline
from regional import (CompanyAccounts, members, directory_profile, discover_members, PUBLIC, regional_bonus, weekly_brief, member_url)
from extended import collaborators, public_record
from funding import import_ymner_csv, ymner_public, verify_links
from data import COMPANIES
from datetime import date

URL='https://www.bluesciencepark.se/medlem/example/'
PAGE={'url':URL,'title':'Example Marine','paragraphs':['Example Marine','Develops marine sensors for industrial applications.','Bransch','Antal anställda','Grundat','Ort','Webb','Marinteknik','11-50','2018','Karlskrona','example.com'],'text':'Example Marine\nDevelops marine sensors for industrial applications.\nBransch\nAntal anställda\nGrundat\nOrt\nWebb\nMarinteknik\n11-50\n2018\nKarlskrona\nexample.com','links':[('https://example.com/','example.com')],'retrieved':'2026-11-13T12:00:00+00:00','sha256':'fixture'}
class RegionalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.s=Store(os.path.join(self.tmp.name,'db.sqlite3'))
    def tearDown(self): self.tmp.cleanup()
    def test_directory_fields(self):
        c=directory_profile(PAGE); self.assertEqual(c['city'],'Karlskrona'); self.assertEqual(c['employees'],'11-50'); self.assertIn('marine',c['tags']); self.assertEqual(c['website'],'https://example.com/'); self.assertTrue(c['evidence'])
    def test_directory_discovery(self):
        with patch('regional.fetch',side_effect=[{'links':[(URL,'Example Marine')]},PAGE]): m=discover_members(self.s)
        self.assertEqual(m['count'],1); self.assertEqual(len(members(self.s)),4); self.assertIn('unverified',m['coverage'])
    def test_member_url_allowlist(self):
        self.assertTrue(member_url(URL)); self.assertFalse(member_url('https://evil.example/medlem/example/')); self.assertFalse(member_url('https://www.bluesciencepark.se/bli-medlem/'))
    def test_company_binding(self):
        a=CompanyAccounts(self.s)
        with patch.dict(os.environ,{'BLUELINK_STAFF_INVITE':'staff-secret'}):
            with self.assertRaises(ValueError): a.staff('staff','password-12345','wrong')
            staff=a.staff('staff','password-12345','staff-secret')
        c=a.provision(staff,'cleura','company-password', 'cleura')
        self.assertEqual(a.login('cleura','company-password')['company_id'],'cleura')
        with self.assertRaises(ValueError): a.provision(staff,'second','company-password','cleura')
        with self.assertRaises(ValueError): a.provision(c,'afry','company-password','afry')
        other=a.provision(staff,'afry','company-password','afry'); self.s.put(c['workspace'],'edit','Cleura',{'secret':'private'})
        self.assertIsNone(self.s.get(other['workspace'],'edit','Cleura'))
    def test_region_and_webinars(self):
        local={'category':'Events','location':'Karlskrona','event_format':'In person / verify'}
        self.assertEqual(regional_bonus(local)[0],3); self.assertEqual(regional_bonus({**local,'location':'Ronneby'})[0],2); self.assertEqual(regional_bonus({**local,'event_format':'Online / verify'})[0],0); self.assertEqual(regional_bonus({**local,'category':'Funding'})[0],0)
    def test_regional_not_irrelevant(self):
        p=baseline(COMPANIES[0]); item={**catalogue()[0],'id':'local','category':'Events','location':'Karlskrona','event_format':'In person / verify','event_date':'2099-01-01','tags':['cloud']}; remote={**item,'id':'remote','location':'Stockholm'}; unrelated={**item,'id':'unrelated','tags':['unrelated']}
        r=rank(p,[remote,unrelated,item]); self.assertEqual([o['id'] for o in r],['local','remote']); self.assertIn('Karlskrona',r[0]['reason'])
    def test_collaboration_regional(self):
        p=baseline(COMPANIES[0]); a={**baseline(COMPANIES[1]),'name':'A','city':'Karlskrona'}; b={**a,'name':'B','city':'Stockholm'}; self.assertEqual(collaborators(p,[b,a])[0]['name'],'A')
    def test_event_location(self):
        page={**PAGE,'structured':[{'@type':'Event','startDate':'2099-01-01','location':{'address':{'addressLocality':'Karlskrona'}}}],'metadata':{}}
        self.assertEqual(public_record(page,'BSP','Events')['location'],'Karlskrona')
    def test_ymner_authorized(self):
        with patch.dict(os.environ,{'BLUELINK_YMNER_PUBLIC_ALLOWED':'0'}): self.assertFalse(ymner_public()[0])
        with self.assertRaises(ValueError): import_ymner_csv('name\nExample')
        self.assertFalse(verify_links(['https://evil.example/calls-for-proposals/a'])[0])
    def test_ymner_verified(self):
        u='https://www.vinnova.se/en/calls-for-proposals/example/'
        with patch('funding.fetch',return_value={**PAGE,'url':u}): r,e=import_ymner_csv('official_url\n'+u)
        self.assertFalse(e); self.assertEqual(r[0]['url'],u); self.assertIn('ymner.com',r[0]['discovery_source'])
    def test_weekly_brief(self): self.assertLessEqual(len(weekly_brief(baseline(COMPANIES[0]),catalogue())),5)
