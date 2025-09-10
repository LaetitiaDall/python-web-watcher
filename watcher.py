#!/usr/bin/env python3
# Minimal: on_modified for *.css/*.js; send RELATIVE path over WebSocket.
# Also seeds MU plugin: copies watcher-connector.php -> <ROOT>/wp-content/mu-plugins/
# and replaces the placeholder #PORT# with the actual port from env.

import os
import shutil
from pathlib import Path
import asyncio
import websockets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ROOT = os.environ.get("WATCH_ROOT", "/var/www/html")
HOST = os.environ.get("WS_HOST", "0.0.0.0")
# Prefer WATCHER_PORT (compose .env used for WP) then WS_PORT; fallback to 12345
PORT = 8787
WS_URL =  os.environ.get("WS_URL") 
EXTS = (".css", ".js")

clients = set()

async def broadcast(text: str):
    dead = []
    for ws in list(clients):
        try:
            await ws.send(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)

async def ws_handler(ws):
    print("client connected")
    clients.add(ws)
    try:
        await ws.wait_closed()
    finally:
        clients.discard(ws)

class Handler(FileSystemEventHandler):
    def __init__(self, root: str, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.root = os.path.abspath(root)
        self.loop = loop

    def on_modified(self, event):
        if event.is_directory:
            return
        path = event.src_path
        if not path.lower().endswith(EXTS):
            return
        try:
            rel = os.path.relpath(path, self.root).replace(os.sep, "/")
        except Exception:
            return

        print(rel)
        asyncio.run_coroutine_threadsafe(broadcast(rel), self.loop)

def seed_mu_plugin(root: str, ws_url: int):
    """
    Copy/overwrite watcher-connector.php (next to this script)
    to <root>/wp-content/mu-plugins/watcher-connector.php.
    Then replace '#WSURL#' with the provided port value.
    """
    script_dir = Path(__file__).resolve().parent
    src = script_dir / "watcher-connector.php"
    dest_dir = Path(root).resolve() / "wp-content" / "mu-plugins"
    dest = dest_dir / "watcher-connector.php"

    try:
        if not src.is_file():
            print(f"[mu-plugins] Source not found: {src}")
            return
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)  # overwrites if exists
        print(f"[mu-plugins] Copied {src} -> {dest}")

        # Replace placeholder
        try:
            text = dest.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = dest.read_text(encoding="latin-1")

        replaced = text.replace("#WSURL#", str(ws_url))
        if replaced != text:
            dest.write_text(replaced, encoding="utf-8")
            print(f"[mu-plugins] Replaced #WSURL# with {ws_url} in {dest.name}")
        else:
            print(f"[mu-plugins] No #WSURL# placeholder found in {dest.name}")

    except Exception as e:
        print(f"[mu-plugins] Copy/replace failed: {e}")

async def main():
    root = os.path.abspath(ROOT)
    if not os.path.isdir(root):
        raise SystemExit(f"Watch root does not exist: {root}")

    # Seed/overwrite the MU plugin before starting the watcher/WS
    seed_mu_plugin(root, WS_URL)

    loop = asyncio.get_running_loop()

    # start watchdog (runs in its own thread)
    handler = Handler(root, loop)
    observer = Observer()
    observer.schedule(handler, root, recursive=True)
    observer.start()

    try:
        async with websockets.serve(ws_handler, HOST, PORT):
            print(f"WebSocket running on ws://{HOST}:{PORT}")
            print(f"Watching {root} (on_modified) for {EXTS}")
            await asyncio.Future()  # run forever
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
