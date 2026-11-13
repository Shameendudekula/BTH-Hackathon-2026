from contextlib import closing
"""Extended agents, account authentication, public change tracking and opt-in digests."""
import hashlib, hmac, secrets, json, os, re, sqlite3, smtplib, ssl
from email.message import EmailMessage
from datetime import date, datetime, timezone, timedelta
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from core import Store, baseline, rank, norm, status
from data import COMPANIES, OPPS
from live import fetch, tags, evidence, allowed, now, profile_live, discover

CATEGORIES=['All','Testing','Funding','Research','News','Events']
# These are deliberately simulated examples, never represented as discovered events or publications.
DEMO=[('demo-paper','Cloud infrastructure research briefing','Research',['cloud','infrastructure'],'Research briefing on efficient cloud infrastructure.'),('demo-news','Industrial energy innovation briefing','News',['energy','engineering','industry'],'Example regional industry development briefing.'),('demo-event','Cybersecurity collaboration workshop','Events',['cybersecurity','OT','security'],'Example workshop for industry security practitioners.')]
def demo_records():
    return [dict(id=i,title=t,category=c,tags=ts,description=d,provider='Simulated demo',url='https://www.bluesciencepark.se/',date='No real publication or event date',deadline=None,event_date=None,event_format='Unconfirmed',eligibility='Illustrative only; not a real opportunity.',next='Refresh public sources for real findings.',retrieved=now(),evidence=[{'quote':'Simulated example; no supporting source. Link is the science park homepage, not evidence.','url':'https://www.bluesciencepark.se/','retrieved':now()}],mode='SIMULATED — not a real finding') for i,t,c,ts,d in DEMO]

# Public Crossref metadata; no invented papers or abstracts. Fixed API endpoint; no arbitrary URLs.
RESEARCH_QUERIES=['cloud infrastructure data centers','industrial cybersecurity operational technology','industrial energy engineering']
def research(limit=4):
    results=[]; errors=[]
    for q in RESEARCH_QUERIES:
        try:
            r=requests.get('https://api.crossref.org/works',params={'query.bibliographic':q,'rows':limit,'filter':'from-pub-date:'+str(date.today()-timedelta(days=730)),'sort':'relevance','select':'DOI,title,published,URL,abstract,subject,publisher'},timeout=(5,15),allow_redirects=False); r.raise_for_status()
            for item in r.json()['message']['items']:
                title=(item.get('title') or [''])[0]; doi=item.get('DOI',''); url=item.get('URL','')
                if not title or not doi or urlparse(url).scheme!='https' or urlparse(url).hostname!='doi.org': continue
                abstract=BeautifulSoup(item.get('abstract') or '', 'html.parser').get_text(' ',strip=True)[:1800]; desc=abstract or title
                detected=tags(title+' '+abstract+' '+' '.join(item.get('subject',[])))
                if not detected: continue
                parts=item.get('published',{}).get('date-parts',[[]])[0]; published='-'.join(f'{x:02d}' for x in parts) if parts else 'Publication date unverified'
                results.append(dict(id='doi-'+hashlib.sha256(doi.encode()).hexdigest()[:16],title=title,category='Research',provider='Crossref',url=url,description=desc,tags=detected,date=published,deadline=None,eligibility='Research metadata only; full text access may be restricted.',next='Read the publication and assess applicability to your company.',retrieved=now(),evidence=[{'quote':title,'url':url,'retrieved':now()}],mode='Live Crossref metadata'))
        except Exception as e: errors.append('Crossref '+q+': '+type(e).__name__)
    return list({x['id']:x for x in results}.values()),errors

LISTS=[('Blue Science Park','https://www.bluesciencepark.se/','Events'),('Blue Science Park','https://www.bluesciencepark.se/','News'),('RISE','https://www.ri.se/en','Events'),('Vinnova','https://www.vinnova.se/en/','News')]
EVENT_PATH=re.compile(r'/(?:events?|evenemang|kalender|calendar|webinar|seminarier)(?:/|$)',re.I)
NEWS_PATH=re.compile(r'/(?:news|nyheter|aktuellt)(?:/|$)',re.I)
def event_metadata(text):
    # Only explicit start/date labels; do not turn publication dates into event dates.
    from live import deadline_from
    m=re.search(r'(?:event date|start date|starts on|event starts|datum|date of event)\s*[:–—-]?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}\s+[A-Za-z]+\s+\d{4}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})',text,re.I)
    d=deadline_from('deadline: '+m.group(1)) if m else None
    online=bool(re.search(r'\b(?:online|webinar|virtual event|digitalt)\b',text,re.I)); onsite=bool(re.search(r'\b(?:in person|on-site|onsite|physical event|på plats)\b',text,re.I))
    return d, 'Hybrid / verify' if online and onsite else 'Online / verify' if online else 'In person / verify' if onsite else 'Unverified'
def public_record(page,provider,category):
    d,fmt=event_metadata(page['text']) if category=='Events' else (None,None)
    published=page.get('metadata',{}).get('article:published_time','')[:10]
    audience='Audience, registration and access: verify with organizer.'
    for obj in page.get('structured',[]):
        if not isinstance(obj,dict): continue
        typ=obj.get('@type',[]); typ=[typ] if isinstance(typ,str) else typ
        if category=='Events' and any(str(t).endswith('Event') for t in typ):
            candidate=str(obj.get('startDate',''))[:10]
            try: d=date.fromisoformat(candidate).isoformat()
            except ValueError: pass
            attendance=str(obj.get('eventAttendanceMode',''))
            if 'OnlineEventAttendanceMode' in attendance: fmt='Online / verify'
            elif 'OfflineEventAttendanceMode' in attendance: fmt='In person / verify'
            elif 'MixedEventAttendanceMode' in attendance: fmt='Hybrid / verify'
            a=obj.get('audience'); a=a.get('audienceType') if isinstance(a,dict) else a
            if isinstance(a,str) and a: audience=a[:300]+'; verify registration with organizer.'
        if not published and obj.get('datePublished'): published=str(obj['datePublished'])[:10]
    try: published=date.fromisoformat(published).isoformat()
    except ValueError: published='Publication date unverified'
    ev=evidence(page)[:4]; desc=' '.join(x['quote'] for x in ev[:2])[:900]
    return dict(id='public-'+hashlib.sha256(page['url'].encode()).hexdigest()[:16],title=page['title'],category=category,provider=provider,url=page['url'],description=desc,tags=tags(page['text']),date=published,deadline=None,event_date=d,event_format=fmt,eligibility=audience if category=='Events' else 'Public information; verify relevance.',next='Review original source and confirm registration details.' if category=='Events' else 'Review the original update and assess business impact.',retrieved=page['retrieved'],evidence=ev,mode='Live public extraction')
def news_events(limit=3):
    results=[]; errors=[]
    for provider,url,cat in LISTS:
        pattern=EVENT_PATH if cat=='Events' else NEWS_PATH
        try:
            page=fetch(url); links=list(dict.fromkeys(u for u,l in page['links'] if l and allowed(u) and pattern.search(urlparse(u).path)))[:limit+2]
            # Follow one listing level; never claim a listing page is an event.
            candidates=[]
            for u in links:
                try:
                    detail=fetch(u); children=[v for v,l in detail['links'] if l and allowed(v) and pattern.search(urlparse(v).path) and urlparse(v).path.rstrip('/').startswith(urlparse(u).path.rstrip('/')+'/')]
                    if children: candidates.extend(children[:limit])
                    elif len(urlparse(u).path.strip('/').split('/'))>=2 and urlparse(u).path.strip('/').split('/')[-1].lower() not in ['news','events','event','nyheter','evenemang','aktuellt','calendar','kalender']: candidates.append(u)
                except Exception as e: errors.append(provider+': '+type(e).__name__+' '+u)
            for u in list(dict.fromkeys(candidates))[:limit]:
                try:
                    rec=public_record(fetch(u),provider,cat)
                    if rec['tags'] and rec['title']: results.append(rec)
                except Exception as e: errors.append(provider+': '+type(e).__name__+' '+u)
        except Exception as e: errors.append(provider+' '+cat+': '+type(e).__name__)
    return list({r['id']:r for r in results}.values()),errors

def collaborators(p,public_profiles):
    out=[]
    for other in public_profiles:
        if other['name']==p['name']: continue
        common=sorted(set(t.lower() for t in p.get('tags',[])) & set(t.lower() for t in other.get('tags',[])))
        # Explicit complementary capability pairs, not claims about partner intent.
        pairs=[(a,b) for a,b in [('cloud','cybersecurity'),('infrastructure','security'),('engineering','cloud'),('industry','OT'),('energy','data centers')] if (a.lower() in {x.lower() for x in p.get('tags',[])} and b.lower() in {x.lower() for x in other.get('tags',[])}) or (b.lower() in {x.lower() for x in p.get('tags',[])} and a.lower() in {x.lower() for x in other.get('tags',[])})]
        if common or pairs: out.append({'name':other['name'],'shared':common,'complementary':pairs,'score':2*len(common)+len(pairs),'url':other['url'],'evidence':other.get('evidence',[]),'next':'Ask Blue Science Park staff for an introduction; interest is not confirmed for either party.'})
    return sorted(out,key=lambda x:(-x['score'],x['name']))

def record_profile(s,w,profile):
    name=profile['name']; old=s.get(w,'public_profile',name); changes=s.get(w,'changes',name,[])
    fingerprint=lambda p: tuple(sorted({e.get('hash') for e in p.get('evidence',[]) if e.get('hash')})) or (hashlib.sha256(p['facts'].encode()).hexdigest(),)
    if old and fingerprint(old)!=fingerprint(profile):
        changes.append({'time':now(),'url':profile['url'],'old_tags':old.get('tags',[]),'new_tags':profile.get('tags',[]),'old_excerpt':old['facts'][:500],'new_excerpt':profile['facts'][:500],'note':'Public extraction changed; human review needed. May be page layout or wording.'}); s.put(w,'changes',name,changes[-50:])
    s.put(w,'public_profile',name,profile)

def merge_records(s,w,results):
    old={o['id']:o for o in s.get(w,'catalogue','live',[])}; new=[]
    for o in results:
        if o['id'] not in old: new.append(o['id'])
        old[o['id']]=o
    s.put(w,'catalogue','live',list(old.values())); return new

def alerts(s,w,company,profile,records):
    seen=set(s.get(w,'alert_seen',company,[])); history=s.get(w,'alerts',company,[])
    for o in rank(profile,[r for r in records if not r.get('mode','').startswith('SIMULATED')]):
        if o['id'] not in seen:
            history.append({'id':o['id'],'title':o['title'],'url':o['url'],'reason':o['reason'],'time':now()}); seen.add(o['id'])
    s.put(w,'alert_seen',company,sorted(seen)); s.put(w,'alerts',company,history[-200:]); return history[-200:]

def refresh_all(s,w,use_ai=False):
    errors=[]
    for c in COMPANIES:
        try: record_profile(s,w,profile_live(c,use_ai))
        except Exception as e: errors.append(c['name']+': '+type(e).__name__)
    results=[]
    for f in [lambda:discover(OPPS,limit=3),research,news_events]:
        r,e=f(); results.extend(r); errors.extend(e)
    merge_records(s,w,results)
    for c in COMPANIES:
        p={**s.get(w,'public_profile',c['name'],baseline(c)),**s.get(w,'edit',c['name'],{})}; alerts(s,w,c['name'],p,results)
    s.put(w,'meta','refresh',{'time':now(),'count':len(results),'errors':errors}); return results,errors

# Password-based accounts; no public workspace recovery token in authenticated mode.
class Accounts:
    def __init__(self,store):
        self.store=store
        with closing(sqlite3.connect(store.path)) as c, c: c.execute('CREATE TABLE IF NOT EXISTS accounts(username TEXT PRIMARY KEY, salt TEXT, digest TEXT, workspace TEXT UNIQUE, role TEXT)')
    @staticmethod
    def digest(password,salt): return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),600000).hex()
    def register(self,username,password,staff_invite=None):
        u=username.strip().lower()
        if not re.fullmatch(r'[a-z0-9_.-]{3,60}',u) or len(password)<12 or len(password)>256: raise ValueError('Username: 3–60 letters/numbers/dot/dash; password: 12–256 characters.')
        role='staff' if staff_invite and os.getenv('BLUELINK_STAFF_INVITE') and hmac.compare_digest(staff_invite,os.environ['BLUELINK_STAFF_INVITE']) else 'member'
        salt=secrets.token_hex(16); digest=self.digest(password,salt); w=self.store.new_workspace()
        try:
            with closing(sqlite3.connect(self.store.path)) as c, c: c.execute('INSERT INTO accounts VALUES(?,?,?,?,?)',(u,salt,digest,w,role))
        except sqlite3.IntegrityError: raise ValueError('Username unavailable')
        return {'username':u,'workspace':w,'role':role}
    def login(self,username,password):
        if len(password)>256: return None
        with closing(sqlite3.connect(self.store.path)) as c, c: row=c.execute('SELECT username,salt,digest,workspace,role FROM accounts WHERE username=?',(username.strip().lower(),)).fetchone()
        calculated=self.digest(password,row[1] if row else '0'*32)
        if not row or not hmac.compare_digest(calculated,row[2]): return None
        return {'username':row[0],'workspace':row[3],'role':row[4]}
    def workspaces(self):
        with closing(sqlite3.connect(self.store.path)) as c, c: return [r[0] for r in c.execute('SELECT workspace FROM accounts')]

def send_digest(s,w):
    prefs=s.get(w,'preferences','email',{}); address=prefs.get('address','')
    if not prefs.get('enabled') or not address: return 'Email not enabled'
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',address): return 'Invalid email address'
    host=os.getenv('BLUELINK_SMTP_HOST'); sender=os.getenv('BLUELINK_SMTP_FROM')
    if not host or not sender: return 'SMTP not configured; in-app alerts remain available'
    sent=set(s.get(w,'preferences','sent',[])); pending=[]
    for c in COMPANIES:
        for a in s.get(w,'alerts',c['name'],[]):
            key=c['name']+':'+a['id']
            if key not in sent: pending.append((key,c['name'],a))
    if not pending: return 'No new alerts'
    msg=EmailMessage(); msg['From']=sender; msg['To']=address; msg['Subject']='BlueLink — innovation opportunity digest'; msg.set_content('\n\n'.join(f"{name}: {a['title']}\n{a['reason']}\n{a['url']}" for _,name,a in pending)+'\n\nPotential matches only; verify original sources. Disable email in BlueLink settings.')
    with smtplib.SMTP(host,int(os.getenv('BLUELINK_SMTP_PORT','587')),timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context()); user=os.getenv('BLUELINK_SMTP_USER'); pw=os.getenv('BLUELINK_SMTP_PASSWORD')
        if user and pw: smtp.login(user,pw)
        smtp.send_message(msg)
    s.put(w,'preferences','sent',sorted(sent|{k for k,_,_ in pending})); return f'Sent {len(pending)} alerts'

def full_assistant(q,p,opps,public_profiles,previous=''):
    from core import assistant
    low=q.lower()
    # Boundaries always evaluated before follow-up routing; no free-form model or external instructions.
    if re.search(r'ignore|override|system prompt|developer message|jailbreak|pretend|act as|forget.*instruction|new role|disregard|reveal.*prompt|private|confidential|secret|password|token|api key|user interactions|guarantee|confirm.*eligib|promise|approve|formal decision|weather|movie|poem|recipe|football|joke|game|homework|stock price',low): return assistant(q,p,opps)
    if re.search(r'\b(?:partner|partners|collaborat\w*)\b',low):
        matches=collaborators(p,public_profiles)
        return '\n\n'.join(f"**{m['name']}** — Shared: {', '.join(m['shared']) or 'none'}; complementary: {', '.join(a+' / '+b for a,b in m['complementary']) or 'none'}. {m['next']} [Public source]({m['url']})" for m in matches) or 'No evidence-based partner match found.'
    # Follow-ups can inherit only a safe category, never prior instructions.
    context=low+' '+previous.lower() if re.fullmatch(r'\s*(?:why|what next|tell me more|more details|how|which one)[?\s]*',low) else low
    for pattern,category in [(r'event|workshop|conference|webinar','Events'),(r'research|paper|publication','Research'),(r'news|trend|market|regional development','News')]:
        if re.search(pattern,context):
            found=rank(p,opps,category)
            return '\n\n'.join(f"**{o['title']}** — {o['mode']}. {o['reason']} {o['next']} [Source]({o['url']})" for o in found[:3]) or 'No matching records. Refresh public sources; no availability is implied.'
    if context!=low and re.search(r'funding|grant|testbed|testing',context): return assistant(context,p,opps)
    return assistant(q,p,opps)
