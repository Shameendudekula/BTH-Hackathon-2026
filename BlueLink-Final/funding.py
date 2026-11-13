"""Ymner discovery via explicitly authorized import or opt-in public links. Official funder verification."""
import csv, io, os
from urllib.parse import urlparse
from live import fetch, allowed, opportunity, now
YMNER='https://www.ymner.com/en/find-financing/grants?status=coming&status=open'

def verify_links(urls):
    results=[]; errors=[]
    for url in list(dict.fromkeys(urls))[:30]:
        try:
            if not allowed(url) or not any(x in urlparse(url).path.lower() for x in ('/calls-for-proposals/','/utlysningar/','/utlysning/')): raise ValueError('Use an approved original funder call URL')
            page=fetch(url); record=opportunity(page,'Original funder via Ymner','Funding'); record['discovery_source']=YMNER; results.append(record)
        except Exception as e: errors.append(url+': '+str(e))
    return results,errors

def import_ymner_csv(text):
    reader=csv.DictReader(io.StringIO(text)); fields=reader.fieldnames or []
    if 'official_url' not in fields: raise ValueError('CSV must contain official_url column; use authorized export or manually verified links.')
    return verify_links([r['official_url'].strip() for r in reader if r.get('official_url')])

def ymner_public():
    if os.getenv('BLUELINK_YMNER_PUBLIC_ALLOWED')!='1': return [],['Ymner automatic retrieval disabled pending permission; use authorized CSV / original funder links.']
    try:
        page=fetch(YMNER)
        return verify_links([u for u,_ in page['links'] if allowed(u) and urlparse(u).hostname not in ('ymner.com','www.ymner.com')])
    except Exception as e: return [],['Ymner: '+type(e).__name__]
