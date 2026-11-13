"""Start BlueLink on an available loopback port; open browser after health check."""
import argparse
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def choose_port(start=8501, count=20):
    for port in range(start, min(start + count, 65536)):
        with socket.socket() as sock:
            try:
                sock.bind(('127.0.0.1', port))
            except OSError:
                continue
            return port
    raise RuntimeError('No available local port. Close unused applications and try again.')

def healthy(url):
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(url+'/_stcore/health', timeout=1) as response:
            return response.status == 200 and response.read().strip() == b'ok'
    except OSError:
        return False

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8501)
    parser.add_argument('--no-browser', action='store_true')
    args=parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('port must be between 1024 and 65535')
    port=choose_port(args.port)
    url=f'http://127.0.0.1:{port}'
    cmd=[sys.executable,'-m','streamlit','run',str(ROOT/'app.py'),'--server.address=127.0.0.1',f'--server.port={port}','--server.headless=true','--browser.gatherUsageStats=false']
    print(f'Starting BlueLink at {url}\nKeep this window open. Press Ctrl+C to stop.',flush=True)
    process=subprocess.Popen(cmd,cwd=ROOT)
    try:
        for _ in range(120):
            if process.poll() is not None:
                print('Streamlit exited before becoming ready. See the error above.',file=sys.stderr)
                return process.returncode or 1
            if healthy(url):
                print(f'BlueLink is ready: {url}',flush=True)
                if not args.no_browser:
                    try: webbrowser.open(url)
                    except Exception as exc: print(f'Open the URL manually: {exc}')
                return process.wait()
            time.sleep(.5)
        print('Server did not become ready. Review the terminal output and try again.',file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: process.kill(); process.wait()

if __name__=='__main__': sys.exit(main())
