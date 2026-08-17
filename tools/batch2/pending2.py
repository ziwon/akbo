#!/usr/bin/env python3
"""현재 data/ 상태를 기준으로 남은 미분류 페이지와 '1페이지짜리 곡'을 대조한다."""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'data'); UNS = os.path.join(DATA, '_미분류 (batch2)')
idx = json.load(open(f'{ROOT}/tools/batch2/index.json'))
lay = {int(k): v for k, v in json.load(open(f'{ROOT}/tools/batch2/layout.json')).items()}
scan = {o["file"]: o for o in json.load(open(f'{ROOT}/tools/scan_new.json', encoding='utf-8'))}
meta = json.load(open(f'{ROOT}/tools/pieces.json', encoding='utf-8'))
notes = {}
for line in open(f'{ROOT}/tools/batch2/notes.md', encoding='utf-8'):
    m = re.match(r'^(\d+)\s+(.*)$', line.rstrip())
    if m: notes[int(m.group(1))] = m.group(2)
name_of_file = {v: int(k) for k, v in idx.items()}

# 남은 미분류
pend = sorted(int(f[1:4]) for f in os.listdir(UNS) if f.endswith('.JPEG'))

# 1페이지짜리 곡 → 그 페이지의 판독 인덱스 찾기 (2차 배치 곡만)
import hashlib
def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''): h.update(c)
    return h.hexdigest()
raw_md5 = {}
for i in range(len(idx)):
    raw_md5.setdefault(md5(os.path.join(ROOT, 'raw', 'added', idx[str(i)])), i)

solo = {}
for p in meta['pieces']:
    d = os.path.join(DATA, p['dir'])
    if not os.path.isdir(d) or p['id'] == 'unsorted-batch2': continue
    fs = [f for f in os.listdir(d) if f.lower().endswith('.jpeg')]
    if len(fs) == 1:
        i = raw_md5.get(md5(os.path.join(d, fs[0])))
        if i is not None: solo[i] = p['title']

def keyof(n):
    m = re.search(r'(?<![\w])(\d)([#b])(?![\w])', n)
    if m: return m.group(1) + m.group(2)
    return 'C' if re.search(r'(?<![A-Za-z])C(?![A-Za-z#b])', n) else '?'

def info(i):
    o = scan[idx[str(i)]]; n = notes.get(i, '')
    pg = re.search(r'\bp(\d+)\b', n); ms = re.search(r'\bm(\d+)\b', n)
    return dict(i=i, w=o['w'], h=o['h'], key=keyof(n), note=n,
                page=int(pg.group(1)) if pg else None,
                meas=int(ms.group(1)) if ms else None,
                L=round(lay[i]['L'], 3), R=round(lay[i]['R'], 3))

b = collections.defaultdict(lambda: {'t': [], 'p': []})
for i, t in solo.items():
    q = info(i); b[(q['w'], q['h'], q['L'], q['R'])]['t'].append((q, t))
for i in pend:
    q = info(i); b[(q['w'], q['h'], q['L'], q['R'])]['p'].append(q)

print(f"남은 미분류 {len(pend)}장 / 1페이지짜리 곡 {len(solo)}개\n")
for k, v in sorted(b.items(), key=lambda kv: -len(kv[1]['p'])):
    if not v['p']: continue
    w, h, L, R = k
    print(f"■ {w}x{h} L={L} R={R}   제목 {len(v['t'])} / 페이지 {len(v['p'])}")
    for q, t in sorted(v['t'], key=lambda x: x[0]['key']):
        print(f"   T #{q['i']:<4}[{q['key']:>2}] {t[:58]}")
    for q in sorted(v['p'], key=lambda x: (x['page'] or 99, x['meas'] or 999)):
        print(f"     #{q['i']:<4}[{q['key']:>2}] p{q['page'] or '?':<3} m{q['meas'] or '?':<4} {q['note'][:48]}")
    print()
