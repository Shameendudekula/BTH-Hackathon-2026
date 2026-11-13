from contextlib import closing
import re, sqlite3, json, secrets
from datetime import date
from pathlib import Path
from data import COMPANIES, OPPS, DATE
from live import now

def baseline(c):
    return {**c,'retrieved':DATE,'mode':'Curated public-source snapshot','evidence':[{'claim':c['facts'],'quote':'Curated paraphrase; verify original page (not a verbatim quotation).','url':c['url'],'retrieved':DATE}],'missing':'Current priorities, projects and collaborations not verified.'}
def catalogue(): return [dict(o,retrieved=DATE,mode='Curated public-source snapshot',evidence=[{'quote':'Curated summary; verify original page.','url':o['url'],'retrieved':DATE}]) for o in OPPS]
def status(o,today=None):
    today=today or date.today(); d=o.get('deadline')
    if o.get('mode','').startswith('SIMULATED'): return 'Simulated — not a real finding'
    if o.get('category')=='Events':
        try:
            event=date.fromisoformat(o.get('event_date') or '')
            return 'Closed' if event<today else 'Event date published — verify registration'
        except ValueError: return 'Event date unverified'
    if o.get('category') in ('Research','News'): return 'Public information — verify relevance'
    if o.get('explicit_closed'): return 'Closed'
    if d:
        try:
            if date.fromisoformat(d)<today: return 'Closed'
            if date.fromisoformat(d)==today: return 'Deadline today — verify time'
            return 'Future deadline — verify open status'
        except ValueError: pass
    return 'Availability unverified' if o['category']=='Testing' else 'Deadline/status unverified'
def norm(s): return set(re.findall(r'[a-z0-9]+',s.lower()))
def matched(term,values):
    t=norm(term); return bool(t) and any(t<=norm(v) for v in values)
def rank(p,opps,category='All',include_closed=False,feedback=None):
    results=[]; feedback=feedback or {}
    for o in opps:
        s=status(o)
        if category!='All' and o['category']!=category: continue
        if s=='Closed' and not include_closed: continue
        a=[t for t in o['tags'] if matched(t,p.get('tags',[]))]; b=[t for t in o['tags'] if matched(t,p.get('interests',[]))]
        if not (a or b): continue
        # Bounded feedback adjustment, never creates a match on its own.
        from regional import regional_bonus
        regional, region_reason=regional_bonus(o)
        score=2*len(a)+3*len(b)+feedback.get(o['id'],0)+regional
        results.append({**o,'status':s,'score':score,'reason':f"Technology overlap: {', '.join(a) or 'none'}; interest overlap: {', '.join(b) or 'none'}; feedback adjustment: {feedback.get(o['id'],0):+d}; regional adjustment: +{regional} ({region_reason})."})
    return sorted(results,key=lambda x:(x['status']=='Closed',-x['score'],x['id']))

def assistant(q,p,opps):
    q=q.lower().strip()
    if re.search(r'ignore|override|system prompt|developer message|jailbreak|pretend|act as|forget.*instruction|new role|disregard|reveal.*prompt',q): return 'I cannot change my role or disclose internal instructions. I can help with science park funding, testing and company interests.'
    if re.search(r'private|confidential|secret|other compan(?:y|ies).*profile|password|token|api key|user interactions',q): return 'I cannot disclose private information or other users’ interactions. Only your selected profile and public opportunities are available here.'
    if re.search(r'guarantee|confirm.*eligib|promise|approve|formal decision',q): return 'A recommendation is not a formal eligibility decision or commitment. Contact the provider or Blue Science Park staff.'
    if re.search(r'weather|movie|poem|recipe|football|joke|game|homework|stock price',q): return 'That request is outside my remit. I help with innovation opportunities, funding, testing and collaboration within the science park.'
    if re.search(r'contact|staff|support',q): return 'For human decisions or support, contact [Blue Science Park](https://www.bluesciencepark.se/).'
    if re.search(r'funding|grant|testbed|testing|opportunit|recommend|profile|interest|partner|collaborat|research|event|market|technology|why',q):
        if re.search(r'partner|collaborat|event|research|market',q) and not re.search(r'funding|grant|testing|testbed',q): return 'This prototype focuses on funding and testing. For other activities contact [Blue Science Park](https://www.bluesciencepark.se/).'
        if 'profile' in q or 'interest' in q: return 'Review the public evidence and edit your technology tags and priorities in Company profile. User edits are not verified public facts.'
        cat='Funding' if re.search(r'funding|grant',q) else 'Testing' if re.search(r'testbed|testing',q) else 'All'
        found=rank(p,opps,cat)
        if not found: return 'No current matching records in this catalogue. Check provider websites for new opportunities; unknown status does not establish availability.'
        return '\n\n'.join(f"**{o['title']}** — {o['reason']} {o['status']}. {o['next']} [Original source]({o['url']})" for o in found[:3])
    return 'Could you clarify how your question relates to your company’s innovation, funding or testing needs?'

class Store:
    def __init__(self,path='bluelink.sqlite3'):
        self.path=path
        with closing(sqlite3.connect(path)) as c, c:
            c.execute('CREATE TABLE IF NOT EXISTS state(workspace TEXT, kind TEXT, key TEXT, value TEXT, PRIMARY KEY(workspace,kind,key))')
    def get(self,w,k,key,default=None):
        with closing(sqlite3.connect(self.path)) as c, c: row=c.execute('SELECT value FROM state WHERE workspace=? AND kind=? AND key=?',(w,k,key)).fetchone()
        return json.loads(row[0]) if row else default
    def put(self,w,k,key,value):
        with closing(sqlite3.connect(self.path)) as c, c: c.execute('INSERT INTO state VALUES(?,?,?,?) ON CONFLICT(workspace,kind,key) DO UPDATE SET value=excluded.value',(w,k,key,json.dumps(value)))
    def delete(self,w,k,key):
        with closing(sqlite3.connect(self.path)) as c, c: c.execute('DELETE FROM state WHERE workspace=? AND kind=? AND key=?',(w,k,key))
    def new_workspace(self):
        token=secrets.token_urlsafe(32); self.put(token,'workspace','exists',True); return token
    def valid(self,token): return isinstance(token,str) and len(token)==43 and self.get(token,'workspace','exists',False) is True
