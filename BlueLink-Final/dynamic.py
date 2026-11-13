"""Live-first catalogue and session-driven refresh coordination (no Streamlit dependency)."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from threading import Lock
from core import Store, catalogue
from extended import refresh_all, demo_records


def refresh_due(meta, hours=6, clock=None):
    if not meta or not meta.get('time'): return True
    try:
        stamp=datetime.fromisoformat(meta['time'].replace('Z','+00:00'))
        if stamp.tzinfo is None: return True
        return (clock or datetime.now(timezone.utc))-stamp >= timedelta(hours=hours)
    except (ValueError, TypeError): return True


def visible_catalogue(live, snapshots=False, simulated=False):
    records={}
    for o in (catalogue() if snapshots else []) + list(live) + (demo_records() if simulated else []):
        if not simulated and o.get('mode','').startswith('SIMULATED'): continue
        if not snapshots and o.get('mode','').startswith('Curated'): continue
        key=o['url'].rstrip('/') if not o.get('mode','').startswith('SIMULATED') else o['id']
        records[key]=o
    return {o['id']:o for o in records.values()}


class RefreshJobs:
    """One job per workspace, bounded process-wide queue; workers never access session state."""
    def __init__(self, workers=2):
        self.pool=ThreadPoolExecutor(max_workers=workers)
        self.lock=Lock(); self.jobs={}; self.capacity=workers*4

    def submit(self, path, workspace, use_ai=False):
        key=(path,workspace)
        with self.lock:
            existing=self.jobs.get(key)
            if existing and not existing.done(): return existing
            for k,f in list(self.jobs.items()):
                if f.done(): self.jobs.pop(k,None)
            if len(self.jobs)>=self.capacity: return None
            future=self.pool.submit(refresh_all,Store(path),workspace,use_ai)
            self.jobs[key]=future
            return future
