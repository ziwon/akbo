#!/usr/bin/env python3
"""groups.json 을 data/ 폴더 구조와 pieces.json 항목으로 반영한다."""
import json, os, re, shutil, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "raw", "added")
DATA = os.path.join(ROOT, "data")
idx = json.load(open(os.path.join(ROOT, 'tools/batch2/index.json')))
groups = json.load(open(os.path.join(ROOT, 'tools/batch2/groups.json'), encoding='utf-8'))
scan = {o["file"]: o for o in json.load(open(os.path.join(ROOT, 'tools/scan_new.json'), encoding='utf-8'))}

notes = {}
for line in open(os.path.join(ROOT, 'tools/batch2/notes.md'), encoding='utf-8'):
    m = re.match(r'^(\d+)\s+(.*)$', line.rstrip())
    if m: notes[int(m.group(1))] = m.group(2)

BAD = '/\\:*?"<>|'
def safe(s):
    s = unicodedata.normalize('NFC', s)
    for c in BAD: s = s.replace(c, '-')
    return re.sub(r'\s+', ' ', s).strip()[:90]

def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    s = re.sub(r'[^a-zA-Z0-9]+', '-', s).strip('-').lower()
    return re.sub(r'-+', '-', s) or 'piece'

existing_dirs = {d for d in os.listdir(DATA) if os.path.isdir(os.path.join(DATA, d))}
meta = json.load(open(os.path.join(ROOT, 'tools/pieces.json'), encoding='utf-8'))
existing_ids = {p['id'] for p in meta['pieces']}

plan = []
for name, ids in list(groups['manual'].items()) + list(groups['auto'].items()):
    folder = safe(name)
    base = slug(name); sid = base; n = 2
    while sid in existing_ids: sid = f"{base}-{n}"; n += 1
    existing_ids.add(sid)
    if folder in existing_dirs: folder = folder + " (2)"
    existing_dirs.add(folder)
    plan.append((folder, sid, name, ids))

# 미배정 페이지 보관용
review = groups['review']

if __name__ == '__main__':
    made = 0
    for folder, sid, name, ids in plan:
        d = os.path.join(DATA, folder); os.makedirs(d, exist_ok=True)
        for n, i in enumerate(ids, 1):
            shutil.copy2(os.path.join(SRC, idx[str(i)]), os.path.join(d, f"p{n}.JPEG"))
            made += 1
    rv = os.path.join(DATA, "_미분류 (batch2)")
    os.makedirs(rv, exist_ok=True)
    for i in review:
        o = scan[idx[str(i)]]
        shutil.copy2(os.path.join(SRC, idx[str(i)]),
                     os.path.join(rv, f"p{i:03d}.JPEG"))
    print(f"{len(plan)}곡 / {made}장 배치, 미분류 {len(review)}장")

    # pieces.json 갱신
    for folder, sid, name, ids in plan:
        note = notes.get(ids[0], '')
        comp = ''
        m = re.search(r'—\s*([^,]+)', note)
        if m: comp = m.group(1).strip()
        meta['pieces'].append({
            "dir": folder, "id": sid, "title": name,
            "composer": comp, "note": "", "tags": []
        })
    meta['pieces'].append({
        "dir": "_미분류 (batch2)", "id": "unsorted-batch2",
        "title": "미분류 — 2차 배치",
        "composer": "곡 배정이 끝나지 않은 페이지 모음",
        "note": "파일명 pNNN 은 판독 인덱스입니다 (tools/batch2/notes.md 참조)",
        "tags": ["미분류"]
    })
    json.dump(meta, open(os.path.join(ROOT, 'tools/pieces.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print(f"pieces.json 총 {len(meta['pieces'])}곡")
