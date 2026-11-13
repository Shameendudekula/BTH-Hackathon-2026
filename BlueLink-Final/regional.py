"""Official member discovery, company account binding, regional relevance and SME briefings."""
import hashlib, hmac, os, re, secrets, sqlite3, json
from contextlib import closing
from urllib.parse import urlparse, urljoin
from datetime import date, datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from data import COMPANIES, MEMBERS
from core import baseline, Store, rank
from live import fetch, tags, now, profile_live, allowed

PUBLIC='public-directory'
CITIES=('Karlskrona','Nättraby','Ronneby','Karlshamn','Olofström','Sölvesborg','Jämjö','Lyckeby','Rödeby','Blekinge')
SEED={c['name']:c for c in COMPANIES}
# Directory profile pages are the only automatically admitted URLs.
def member_url(url):
    p=urlparse(url)
    return p.scheme=='https' and p.hostname in ('www.bluesciencepark.se','bluesciencepark.se') and not p.username and not p.password and p.port in (None,443) and bool(re.fullmatch(r'/medlem/[^/]+/?',p.path))

def member_key(url): return urlparse(url).path.strip('/').split('/')[-1].lower()
def identity(name): return re.sub(r'[^a-z0-9]','',name.casefold())
def members(s):
    found=s.get(PUBLIC,'directory','members',[])
    # Merge seed companies by name, preserving established account keys.
    out={identity(c['name']):dict(c,id=identity(c['name'])) for c in COMPANIES}
    for c in found:
        k=identity(c['name']); old=out.get(k,{}); out[k]={**old,**c,'name':old.get('name',c['name']),'id':k,'website':c.get('website') or old.get('url','')}
    return sorted(out.values(),key=lambda c:c['name'].casefold())

def directory_profile(page):
    name=page['title'].strip(); name=re.sub(r'\s*[-|–]\s*Blue Science Park.*$','',name,flags=re.I).strip()
    if not name or not member_url(page['url']): raise ValueError('Not a member detail page')
    ps=page['paragraphs']; text=page['text']; fields={}
    # The directory publishes a labelled field table. Its flattened list is also supported.
    labels=['Bransch','Antal anställda','Grundat','Ort','Webb']
    for label in labels:
        m=re.search(r'(?im)^'+re.escape(label)+r'\s*[:–-]\s*(.+)$',text)
        if m: fields[label]=m.group(1).strip()
    for i in range(len(ps)-len(labels)*2+1):
        if [x.strip().casefold() for x in ps[i:i+5]]==[x.casefold() for x in labels]: fields.update(dict(zip(labels,ps[i+5:i+10]))); break
    city=fields.get('Ort','Not explicitly established'); industry=fields.get('Bransch','Not explicitly established')
    desc=[]
    for p in ps:
        if p.strip() in labels or p.strip()==name or 'Fler medlemmar' in p: 
            if 'Fler medlemmar' in p: break
            continue
        if len(p)>25 and not re.search(r'^(Till medlemmar|Blue Science Park|Läs mer)',p,re.I): desc.append(p)
        if len(desc)>=2: break
    fact=' '.join(desc)[:800] or 'Public member listing; business description requires review.'
    # External website links are shown, not fetched until explicitly allowlisted by operator.
    website=''
    declared=fields.get('Webb','').strip().lower().removeprefix('www.')
    for u,l in page.get('links',[]):
        h=urlparse(u).hostname or ''
        if urlparse(u).scheme=='https' and declared and (h.lower().removeprefix('www.')==declared or l.strip().lower().removeprefix('www.')==declared): website=u; break
    ev=[{'claim':fact,'quote':fact,'url':page['url'],'retrieved':page['retrieved'],'hash':page['sha256']}]
    for k,v in fields.items(): ev.append({'claim':k+': '+v,'quote':v,'url':page['url'],'retrieved':page['retrieved']})
    ts=tags(fact+' '+industry)
    # Swedish directory vocabulary.
    for term,tag in [('cybersäkerhet','cybersecurity'),('hosting','cloud'),('marinteknik','marine'),('fartyg','marine'),('energi','energy'),('industri','industry'),('mjukvaru','software'),('iot','IoT'),('provning','testing'),('infrastruktur','infrastructure')]:
        if term in (fact+' '+industry).lower() and tag not in ts: ts.append(tag)
    return dict(name=name,id=identity(name),url=page['url'],website=website,city=city,industry=industry,employees=fields.get('Antal anställda','Unknown'),facts=fact,tags=ts,interests=[t+' opportunities' for t in ts],market='Not explicitly established',geography=city,mode='Live official directory extraction',retrieved=page['retrieved'],evidence=ev,missing='Products, markets, priorities and collaborations require company review; directory may include partners.')

def discover_members(s,limit=100,extra_urls=()):
    """Follow public member detail links and related-member links; no private AJAX bypass."""
    first=fetch(MEMBERS); queue=list(dict.fromkeys([u for u,_ in first['links'] if member_url(u)]+[u.strip() for u in extra_urls if member_url(u.strip())])); seen=set(); found={identity(c['name']):c for c in s.get(PUBLIC,'directory','members',[])}; errors=[]
    # Public listing pagination, when exposed as links.
    for u,_ in first['links']:
        if urlparse(u).hostname==urlparse(MEMBERS).hostname and re.search(r'/bli-medlem/(?:page/\d+/?|\?[^#]*paged=\d+)',u):
            try: queue.extend(v for v,_ in fetch(u)['links'] if member_url(v))
            except Exception as e: errors.append('Pagination: '+type(e).__name__)
    while queue and len(seen)<limit:
        batch=[]
        while queue and len(batch)<4 and len(seen)<limit:
            u=queue.pop(0); k=member_key(u)
            if k not in seen: seen.add(k); batch.append(u)
        def work(u):
            try: return fetch(u),None
            except Exception as e: return None,u+': '+type(e).__name__
        with ThreadPoolExecutor(max_workers=4) as pool:
            for page,error in pool.map(work,batch):
                if error: errors.append(error); continue
                try:
                    c=directory_profile(page); found[c['id']]=c
                    queue.extend(u for u,_ in page['links'] if member_url(u) and member_key(u) not in seen)
                except Exception as e: errors.append('Member parsing: '+type(e).__name__)
        s.put(PUBLIC,'directory','members',list(found.values()))
    meta={'time':now(),'count':len(found),'attempted':len(seen),'errors':errors,'coverage':'Partial / unverified; public links may not expose every member. Staff can review coverage against official directory.'}
    s.put(PUBLIC,'directory','status',meta); return meta

def public_baseline(c): return c if c.get('mode') else baseline(c)
def public_profile(s,c): return s.get(PUBLIC,'public_profile',c['name'],public_baseline(c))
def refresh_company(s,c,use_ai=False):
    from extended import record_profile
    # Seed sites are pre-approved; directory members use official detail plus operator-approved external host.
    if c.get('mode'):
        fresh=directory_profile(fetch(c['url'])); fresh['name']=c['name']; website=fresh.get('website') or c.get('website')
        if website and allowed(website):
            detail=profile_live({**fresh,'url':website},use_ai)
            fresh={**fresh,**detail,'url':c['url'],'website':website,'city':fresh['city'],'evidence':fresh['evidence']+detail['evidence']} 
    else: fresh=profile_live(c,use_ai)
    record_profile(s,PUBLIC,fresh); return fresh

class CompanyAccounts:
    """Staff provisions exactly one account per company. No public claim-by-name registration."""
    def __init__(self,s):
        self.s=s
        with closing(sqlite3.connect(s.path)) as c,c:
            c.execute('CREATE TABLE IF NOT EXISTS company_accounts (username TEXT PRIMARY KEY, company_id TEXT UNIQUE, salt TEXT NOT NULL, digest TEXT NOT NULL, workspace TEXT UNIQUE NOT NULL, role TEXT NOT NULL)')
    @staticmethod
    def digest(p,salt): return hashlib.pbkdf2_hmac('sha256',p.encode(),bytes.fromhex(salt),600000).hex()
    def _register(self,u,p,company_id,role):
        u=u.strip().lower()
        if not re.fullmatch(r'[a-z0-9_.-]{3,60}',u) or not 12<=len(p)<=256: raise ValueError('Username 3–60 letters/numbers/dot/dash; password 12–256 characters.')
        salt=secrets.token_hex(16); w=secrets.token_urlsafe(32)
        try:
            with closing(sqlite3.connect(self.s.path)) as c,c:
                c.execute('INSERT INTO company_accounts VALUES(?,?,?,?,?,?)',(u,company_id,salt,self.digest(p,salt),w,role))
                c.execute('INSERT INTO state VALUES(?,?,?,?)',(w,'workspace','exists','true'))
        except sqlite3.IntegrityError: raise ValueError('Username or company already has an account.')
        return {'username':u,'company_id':company_id,'workspace':w,'role':role}
    def staff(self,u,p,invite):
        secret=os.getenv('BLUELINK_STAFF_INVITE','')
        if not secret or not hmac.compare_digest(invite,secret): raise ValueError('Valid staff invitation required.')
        return self._register(u,p,None,'staff')
    def provision(self,actor,u,p,company_id):
        with closing(sqlite3.connect(self.s.path)) as c:
            ok=c.execute("SELECT 1 FROM company_accounts WHERE workspace=? AND role='staff'",(actor.get('workspace'),)).fetchone()
        if not ok: raise ValueError('Staff authorization required.')
        if company_id not in {c['id'] for c in members(self.s)}: raise ValueError('Unknown member.')
        return self._register(u,p,company_id,'member')
    def login(self,u,p):
        if len(p)>256: return None
        with closing(sqlite3.connect(self.s.path)) as c: row=c.execute('SELECT username,company_id,salt,digest,workspace,role FROM company_accounts WHERE username=?',(u.strip().lower(),)).fetchone()
        result=self.digest(p,row[2] if row else '0'*32)
        if not row or not hmac.compare_digest(result,row[3]): return None
        return dict(username=row[0],company_id=row[1],workspace=row[4],role=row[5])
    def all(self):
        with closing(sqlite3.connect(self.s.path)) as c: return [dict(username=u,company_id=i,workspace=w,role=r) for u,i,w,r in c.execute('SELECT username,company_id,workspace,role FROM company_accounts')]

def region_label(text):
    for city in CITIES:
        if re.search(r'(?<!\w)'+re.escape(city)+r'(?!\w)',str(text),re.I): return city
    return 'Unverified location'
def regional_bonus(o):
    if o.get('category') not in ('Events','Testing','Partners'): return 0,'No location weighting for this category'
    fmt=str(o.get('event_format','')).lower()
    if 'online' in fmt or 'hybrid' in fmt: return 0,'Online/hybrid access: no geographic penalty'
    loc=region_label(o.get('location',''))
    return (3,'Karlskrona proximity') if loc=='Karlskrona' else (2,'Blekinge proximity') if loc!='Unverified location' else (0,'Location not verified as local')

def weekly_brief(p,records,feedback=None,limit=5):
    return rank(p,records,feedback=feedback)[:limit]
