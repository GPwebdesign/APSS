#!/usr/bin/env python3
# coding=utf-8
"""
APSS — Assembla sequenza JPG in video MP4
Uso: python3 frames_to_mp4.py <cartella_frames> [fps]
Esempio: python3 frames_to_mp4.py save/video_20260420_161523 15
"""
import sys
import os
import glob
import cv2

def frames_to_mp4(frames_dir, fps=15):
    frames = sorted(glob.glob(os.path.join(frames_dir, 'frame_*.jpg')))
    if not frames:
        print(f'Nessun frame trovato in {frames_dir}')
        return

    first = cv2.imread(frames[0])
    h, w = first.shape[:2]

    out_path = frames_dir.rstrip('/') + '.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, float(fps), (w, h))

    for i, f in enumerate(frames):
        frame = cv2.imread(f)
        if frame is not None:
            writer.write(frame)
        if i % 50 == 0:
            print(f'Frame {i+1}/{len(frames)}...')

    writer.release()
    print(f'Video salvato: {out_path} ({len(frames)} frame a {fps} FPS)')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Uso: python3 frames_to_mp4.py <cartella_frames> [fps]')
        sys.exit(1)
    fps = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    frames_to_mp4(sys.argv[1], fps)
