#!/usr/bin/env python3
import urllib.request
import io
import time

STREAM_URL = "http://192.168.1.158:6500/video_feed"

print(f"Connessione a {STREAM_URL}...")
try:
    stream = urllib.request.urlopen(STREAM_URL, timeout=5)
    print(f"Connesso! Content-Type: {stream.headers.get('Content-Type')}")
    buf = b""
    frame_count = 0
    t_start = time.time()
    while frame_count < 10:
        chunk = stream.read(4096)
        if not chunk:
            break
        buf += chunk
        start = buf.find(b'\xff\xd8')
        end   = buf.find(b'\xff\xd9')
        if start != -1 and end != -1 and end > start:
            jpg = buf[start:end + 2]
            buf = buf[end + 2:]
            frame_count += 1
            print(f"Frame {frame_count}: {len(jpg)} bytes")
    elapsed = time.time() - t_start
    print(f"\n{frame_count} frame in {elapsed:.1f}s = {frame_count/elapsed:.1f} FPS")
except Exception as e:
    print(f"Errore: {e}")
