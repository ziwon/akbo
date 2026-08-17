#!/usr/bin/env python3
"""미배정 페이지와 '제목만 있는 곡'을 크기 지문별로 나란히 보여준다."""
import json, re, collections, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
idx = json.load(open(f'{ROOT}/tools/batch2/index.json'))
scan = {o["file"]: o for o in json.load(open(f'{ROOT}/tools/scan_new.json', encoding='utf-8'))}
groups = json.load(open(f'{ROOT}/tools/batch2/groups.json', encoding='utf-8'))
notes = {}
for line in open(f'{ROOT}/tools/batch2/notes.md', encoding='utf-8'):
    m = re.match(r'^(\d+)\s+(.*)$', line.rstrip())
    if m: notes[int(m.group(1))] = m.group(2)

def keyof(n):
    m = re.search(r'(?<![\w])(\d)([#b])(?![\w])', n)
    if m: return m.group(1) + m.group(2)
    return 'C' if re.search(r'(?<![A-Za-z])C(?![A-Za-z#b])', n) else '?'

def info(i):
    o = scan[idx[str(i)]]; n = notes.get(i, '')
    pg = re.search(r'\bp(\d+)\b', n); ms = re.search(r'\bm(\d+)\b', n)
    wm = re.search(r'wm=([^\s,]+)', n)
    return dict(i=i, w=o["w"], h=o["h"], note=n, key=keyof(n),
                page=int(pg.group(1)) if pg else None,
                meas=int(ms.group(1)) if ms else None,
                wm=wm.group(1) if wm else '')

# 이미 채워진 곡(2장 이상)은 제외, 제목만 있는 곡(1장)만 후보로
solo = {v[0]: k for k, v in groups['auto'].items() if len(v) == 1}
pend = groups['review']

b = collections.defaultdict(lambda: {"titles": [], "pages": []})
for i, name in solo.items():
    p = info(i); b[(p["w"], p["h"])]["titles"].append((p, name))
for i in pend:
    p = info(i); b[(p["w"], p["h"])]["pages"].append(p)

only = sys.argv[1] if len(sys.argv) > 1 else None
for (w, h), v in sorted(b.items(), key=lambda kv: -len(kv[1]["pages"])):
    if not v["pages"]: continue
    tag = f"{w}x{h}"
    if only and only != tag: continue
    print(f"\n===== {tag}  제목 {len(v['titles'])}곡 / 미배정 {len(v['pages'])}장 =====")
    for p, name in sorted(v["titles"], key=lambda t: t[0]["key"]):
        print(f"  T #{p['i']:<4}[{p['key']:>2}] {name[:56]}")
    print("  " + "-" * 60)
    for p in sorted(v["pages"], key=lambda x: (x["page"] or 99, x["meas"] or 999)):
        print(f"    #{p['i']:<4}[{p['key']:>2}] p{p['page'] or '?':<3} m{p['meas'] or '?':<4} {p['wm']:<16} {p['note'][:44]}")
