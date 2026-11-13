"""External scheduler entry point; refresh every registered account, optionally send opt-in digests."""
import os
from pathlib import Path
from core import Store
from extended import Accounts, refresh_all, send_digest

def main():
    s=Store(str(Path(__file__).resolve().parent / "bluelink.sqlite3")); accounts=Accounts(s)
    for w in accounts.workspaces():
        try:
            records,errors=refresh_all(s,w,os.getenv('BLUELINK_USE_AI')=='1')
            print(f'Refreshed {len(records)} records; {len(errors)} source errors')
            if os.getenv('BLUELINK_SEND_DIGEST')=='1': print(send_digest(s,w))
        except Exception as e: print('Workspace refresh failed:',type(e).__name__)
if __name__=='__main__': main()
