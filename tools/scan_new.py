#!/usr/bin/env python3
"""신규 페이지에서 제목 후보 텍스트와 크기 지문을 뽑는다.

제목 페이지 판별: 상단 17% 를 OCR 해서 '진짜 단어처럼 보이는' 토큰 수를 센다.
악보 본문은 이음줄·기둥이 잡음으로 읽혀 단어가 거의 안 잡히므로 잘 갈린다.
(기존 121장 검증: 제목 38/41 검출, 본문 오검출 2/80)
"""
import csv, io, json, os, re, subprocess, sys
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = "/tmp/claude-1000/scan_new"
os.makedirs(TMP, exist_ok=True)
VOW = re.compile(r"[aeiouAEIOU]")
WORD = re.compile(r"^[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’.\-]{2,}$")


def scan(path, frac=0.17, scale=2):
    with Image.open(path) as im:
        w, h = im.size
        g = ImageOps.autocontrast(im.convert("L").crop((0, 0, w, int(h * frac))))
        g = g.resize((w * scale, int(h * frac) * scale), Image.LANCZOS)
    p = os.path.join(TMP, "t.png"); g.save(p)
    r = subprocess.run(["tesseract", p, "stdout", "--psm", "6", "-l", "eng", "tsv"],
                       capture_output=True, text=True)
    rows = list(csv.DictReader(io.StringIO(r.stdout), delimiter="\t", quoting=csv.QUOTE_NONE))
    good, raw = [], []
    for x in rows:
        t = (x.get("text") or "").strip()
        if not t:
            continue
        try: conf = float(x.get("conf") or -1)
        except ValueError: conf = -1
        raw.append(t)
        if conf >= 62 and WORD.match(t) and VOW.search(t):
            good.append((int(x["top"]), int(x["left"]), t))
    good.sort()
    return w, h, len(good), " ".join(t for _, _, t in good[:14]), " ".join(raw[:24])


def main():
    src = os.path.join(ROOT, "raw", "added")
    skip = set()
    rep = os.path.join(ROOT, "tools", "dedup_report.json")
    if os.path.exists(rep):
        d = json.load(open(rep, encoding="utf-8"))
        skip = {os.path.basename(e["file"]) for e in d["dup_vs_library"] + d["dup_within_new"]}

    files = sorted(f for f in os.listdir(src)
                   if f.lower().endswith((".jpeg", ".jpg", ".png")) and f not in skip)
    out = []
    for i, f in enumerate(files, 1):
        w, h, n, words, raw = scan(os.path.join(src, f))
        out.append({"file": f, "w": w, "h": h, "words": n, "text": words, "raw": raw})
        if i % 25 == 0 or i == len(files):
            print(f"  {i}/{len(files)}", file=sys.stderr, flush=True)

    json.dump(out, open(os.path.join(ROOT, "tools", "scan_new.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    t = sum(1 for o in out if o["words"] >= 2)
    print(f"\n{len(out)}장 스캔 | 제목 후보 {t}장 -> tools/scan_new.json")


if __name__ == "__main__":
    main()
