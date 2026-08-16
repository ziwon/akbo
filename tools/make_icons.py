#!/usr/bin/env python3
"""앱 아이콘 생성 — 오선지 위의 잎사귀."""
from PIL import Image, ImageDraw
import os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "icons")
os.makedirs(OUT, exist_ok=True)

BG = (18, 20, 26)
LEAF = (143, 191, 122)
STAFF = (58, 66, 60)
S = 1024


def draw(size, pad_ratio):
    im = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(im)
    p = S * pad_ratio                      # maskable 여백
    inner = S - 2 * p

    # 오선지 (5줄)
    for i in range(5):
        y = p + inner * (0.30 + i * 0.10)
        d.line([(p + inner * 0.10, y), (p + inner * 0.90, y)], fill=STAFF, width=int(S * 0.016))

    # 잎사귀 — 두 개의 원호가 만나는 렌즈 형태
    cx, cy = p + inner * 0.52, p + inner * 0.47
    w, h = inner * 0.46, inner * 0.62
    pts_a, pts_b = [], []
    for i in range(61):
        t = i / 60
        x = -w / 2 + w * t
        k = math.sin(math.pi * t)
        pts_a.append((cx + x * 0.92 - h * 0.16, cy - x * 0.55 - k * h * 0.30))
        pts_b.append((cx + x * 0.92 - h * 0.16, cy - x * 0.55 + k * h * 0.30))
    d.polygon(pts_a + pts_b[::-1], fill=LEAF)

    # 잎맥 + 줄기
    d.line([pts_a[0], pts_a[-1]], fill=BG, width=int(S * 0.018))
    d.line([pts_a[0], (pts_a[0][0] - inner * 0.16, pts_a[0][1] + inner * 0.20)],
           fill=LEAF, width=int(S * 0.036))
    return im.resize((size, size), Image.LANCZOS)


draw(192, 0.10).save(os.path.join(OUT, "icon-192.png"))
draw(512, 0.10).save(os.path.join(OUT, "icon-512.png"))
draw(512, 0.20).save(os.path.join(OUT, "maskable-512.png"))
draw(180, 0.10).save(os.path.join(OUT, "apple-touch-icon.png"))
print("icons ->", OUT)
