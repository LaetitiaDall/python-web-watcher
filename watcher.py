#!/usr/bin/env python3
# Minimal: on_modified for *.css/*.js; send RELATIVE path over WebSocket.

import os
import asyncio
import websockets
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

ROOT = os.environ.get("WATCH_ROOT", "/var/www/html")
HOST = os.environ.get("WS_HOST", "0.0.0.0")
PORT = int(os.environ.get("WS_PORT", "12345"))
EXTS = (".css", ".js")

clients = set()

async def broadcast(text: str):
    dead = []
    for ws in clients:
        try:
            await ws.send(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        clients.discard(ws)

async def ws_handler(ws):
    print('client connected')
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
        # schedule coroutine from watchdog's thread
        asyncio.run_coroutine_threadsafe(broadcast(rel), self.loop)

async def main():
    root = os.path.abspath(ROOT)
    if not os.path.isdir(root):
        raise SystemExit(f"Watch root does not exist: {root}")

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
