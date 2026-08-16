#!/usr/bin/env python3
"""data/ 의 악보 이미지를 웹용으로 변환하고 site/ 를 빌드합니다.

  python3 tools/build.py            전체 빌드 (변경분만 재변환)
  python3 tools/build.py --force    전부 다시 변환
"""
import json, os, re, shutil, sys, hashlib
from datetime import datetime, timezone
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SITE = os.path.join(ROOT, "site")
OUT_SCORES = os.path.join(SITE, "scores")
META = os.path.join(ROOT, "tools", "pieces.json")

QUALITY = 82          # 육안 무손실 수준 (q80~q88 비교 결과)
COVER_W = 420         # 목록 썸네일 가로 폭
FORCE = "--force" in sys.argv


def page_sort_key(name):
    """p1, p2 … p10 / p1_a, p1_b 를 사람이 기대하는 순서로."""
    m = re.match(r"p(\d+)(?:_([a-z]))?", name)
    if not m:
        return (9999, "z", name)
    return (int(m.group(1)), m.group(2) or "", name)


def convert(src, dst, max_w=None):
    """변경이 있을 때만 WebP 로 변환. (w, h) 반환."""
    if not FORCE and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        with Image.open(dst) as im:
            return im.size
    with Image.open(src) as im:
        im = im.convert("RGB")
        if max_w and im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        im.save(dst, "WEBP", quality=QUALITY, method=6)
        return im.size


def main():
    meta = json.load(open(META, encoding="utf-8"))
    by_dir = {p["dir"]: p for p in meta["pieces"]}

    on_disk = sorted(d for d in os.listdir(DATA) if os.path.isdir(os.path.join(DATA, d)))
    unknown = [d for d in on_disk if d not in by_dir]
    orphan = [d for d in by_dir if d not in on_disk]
    if unknown:
        print(f"  ! pieces.json 에 없는 폴더: {unknown}")
    if orphan:
        print(f"  ! data/ 에 없는 메타데이터: {orphan}")

    pieces, total_bytes = [], 0
    for d in on_disk:
        info = by_dir.get(d)
        if not info:
            continue
        src_dir = os.path.join(DATA, d)
        page_files = sorted(
            (f for f in os.listdir(src_dir) if f.lower().endswith((".jpeg", ".jpg", ".png"))),
            key=page_sort_key,
        )
        if not page_files:
            continue

        pid = info["id"]
        dst_dir = os.path.join(OUT_SCORES, pid)
        pages = []
        for f in page_files:
            stem = os.path.splitext(f)[0]
            dst = os.path.join(dst_dir, stem + ".webp")
            w, h = convert(os.path.join(src_dir, f), dst)
            total_bytes += os.path.getsize(dst)
            pages.append({"src": f"scores/{pid}/{stem}.webp", "w": w, "h": h, "label": stem})

        cover = os.path.join(dst_dir, "cover.webp")
        cw, ch = convert(os.path.join(src_dir, page_files[0]), cover, max_w=COVER_W)
        total_bytes += os.path.getsize(cover)

        pieces.append({
            "id": pid,
            "title": info["title"],
            "composer": info.get("composer", ""),
            "note": info.get("note", ""),
            "tags": info.get("tags", []),
            "incomplete": meta.get("incomplete", {}).get(pid, ""),
            "cover": {"src": f"scores/{pid}/cover.webp", "w": cw, "h": ch},
            "pages": pages,
        })

    pieces.sort(key=lambda p: p["title"].lower())
    library = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pieceCount": len(pieces),
        "pageCount": sum(len(p["pages"]) for p in pieces),
        "pieces": pieces,
    }
    os.makedirs(SITE, exist_ok=True)
    lib_path = os.path.join(SITE, "library.json")
    with open(lib_path, "w", encoding="utf-8") as fh:
        json.dump(library, fh, ensure_ascii=False, separators=(",", ":"))

    # Service Worker 가 참조할 버전 = 라이브러리 내용 해시
    ver = hashlib.sha256(open(lib_path, "rb").read()).hexdigest()[:12]
    with open(os.path.join(SITE, "version.json"), "w") as fh:
        json.dump({"version": ver, "generated": library["generated"]}, fh)

    # 변환 결과에 없는 곡 폴더 청소 (id 변경/곡 삭제 시)
    live = {p["id"] for p in pieces}
    if os.path.isdir(OUT_SCORES):
        for stale in set(os.listdir(OUT_SCORES)) - live:
            shutil.rmtree(os.path.join(OUT_SCORES, stale))
            print(f"  - 삭제: scores/{stale}")

    print(f"{len(pieces)}곡 / {library['pageCount']}페이지 / 이미지 {total_bytes/1024/1024:.1f} MB")
    print(f"version {ver} -> {SITE}")


if __name__ == "__main__":
    main()
