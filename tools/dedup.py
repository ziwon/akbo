#!/usr/bin/env python3
"""악보 이미지 중복 검출.

  md5   : 바이트 동일 (같은 파일 복사본)
  dhash : 256bit 지각 해시 — 같은 페이지를 다른 크기/화질로 다시 캡처한 경우까지 잡는다.
          악보는 흰 바탕에 검은 선이라 64bit 로는 서로 다른 페이지끼리 충돌한다.
"""
import hashlib, json, os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 17, 16          # 인접 픽셀 비교 → 16*16 = 256 bit
THRESH = 12            # 256bit 중 12비트 이내면 같은 페이지로 본다


def dhash(path):
    with Image.open(path) as im:
        g = im.convert("L").resize((W, H), Image.LANCZOS)
        px = list(g.getdata())
    bits = 0
    for y in range(H):
        row = y * W
        for x in range(W - 1):
            bits = (bits << 1) | (px[row + x] > px[row + x + 1])
    return bits


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(root, rel=""):
    out = []
    for dirpath, _, files in os.walk(root):
        for f in sorted(files):
            if f.lower().endswith((".jpeg", ".jpg", ".png", ".webp")):
                p = os.path.join(dirpath, f)
                out.append((os.path.relpath(p, ROOT), p))
    return out


def main():
    lib = scan(os.path.join(ROOT, "data"))
    new = scan(os.path.join(ROOT, "raw", "added"))
    print(f"기존 {len(lib)}장 / 신규 {len(new)}장 해시 계산 중…", file=sys.stderr)

    def build(items):
        return [{"rel": r, "path": p, "md5": md5(p), "dh": dhash(p)} for r, p in items]

    L, N = build(lib), build(new)

    lib_md5 = {}
    for e in L:
        lib_md5.setdefault(e["md5"], []).append(e["rel"])

    dup_lib, dup_new, uniq = [], [], []
    kept = []                       # 신규 중 살아남은 것 (신규끼리 비교용)
    for e in N:
        hit = None
        if e["md5"] in lib_md5:
            hit = ("md5", lib_md5[e["md5"]][0], 0)
        else:
            for l in L:
                d = bin(e["dh"] ^ l["dh"]).count("1")
                if d <= THRESH:
                    hit = ("dhash", l["rel"], d); break
        if hit:
            dup_lib.append({"file": e["rel"], "by": hit[0], "same_as": hit[1], "dist": hit[2]})
            continue

        hit2 = None
        for k in kept:
            if k["md5"] == e["md5"]:
                hit2 = ("md5", k["rel"], 0); break
            d = bin(e["dh"] ^ k["dh"]).count("1")
            if d <= THRESH:
                hit2 = ("dhash", k["rel"], d); break
        if hit2:
            dup_new.append({"file": e["rel"], "by": hit2[0], "same_as": hit2[1], "dist": hit2[2]})
        else:
            kept.append(e); uniq.append(e["rel"])

    res = {"lib_count": len(L), "new_count": len(N),
           "dup_vs_library": dup_lib, "dup_within_new": dup_new, "unique": uniq}
    json.dump(res, open(os.path.join(ROOT, "tools", "dedup_report.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n기존 라이브러리와 중복 : {len(dup_lib)}장")
    print(f"신규 파일끼리 중복     : {len(dup_new)}장")
    print(f"실제 새 페이지         : {len(uniq)}장")


if __name__ == "__main__":
    main()
