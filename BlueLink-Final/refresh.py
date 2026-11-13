from deployment import database_path
"""External scheduler entry point; refresh every registered account, optionally send opt-in digests."""
import os
from pathlib import Path
from core import Store
from extended import refresh_all, send_digest
from regional import CompanyAccounts

def main():
    s=Store(database_path()); accounts=CompanyAccounts(s)
    for a in accounts.all():
        w=a['workspace']
        try:
            records,errors=refresh_all(s,w,os.getenv('BLUELINK_USE_AI')=='1')
            print(f'Refreshed {len(records)} records; {len(errors)} source errors')
            if os.getenv('BLUELINK_SEND_DIGEST')=='1': print(send_digest(s,w))
        except Exception as e: print('Workspace refresh failed:',type(e).__name__)
if __name__=='__main__': main()
