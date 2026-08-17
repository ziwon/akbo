#!/usr/bin/env python3
"""판독 노트를 구조화해 곡별로 자동 그룹핑한다.

규칙: 같은 (w,h) 지문 버킷 안에서 제목 페이지(p1)를 기준으로
      페이지번호 2,3,4… 가 순서대로 이어지고 첫 마디번호가 단조 증가하면 같은 곡.
확신이 없는 페이지는 배정하지 않고 review 로 남긴다.
"""
import json, re, collections, sys

idx = json.load(open('tools/batch2/index.json'))
scan = {o["file"]: o for o in json.load(open('tools/scan_new.json', encoding='utf-8'))}

notes = {}
for line in open('tools/batch2/notes.md', encoding='utf-8'):
    m = re.match(r'^(\d+)\s+(.*)$', line.rstrip())
    if m:
        notes[int(m.group(1))] = m.group(2)

P = {}
for i in range(len(idx)):
    o = scan[idx[str(i)]]
    n = notes.get(i, '')
    title = None
    tm = re.match(r'^T\s+"([^"]+)"(.*)$', n)
    if tm:
        title = tm.group(1)
    pg = re.search(r'\bp(\d+)\b', n)
    ms = re.search(r'\bm(\d+)\b', n)
    wm = re.search(r'wm=([^\s,]+)', n)
    hdr = re.search(r'헤더 "?([^"→,]+)"?', n)
    arrow = re.search(r'→\s*(\d+)', n)
    P[i] = dict(i=i, w=o["w"], h=o["h"], note=n, title=title,
                page=int(pg.group(1)) if pg else None,
                meas=int(ms.group(1)) if ms else None,
                wm=wm.group(1) if wm else None,
                hdr=hdr.group(1).strip() if hdr else None,
                to=int(arrow.group(1)) if arrow else None)

# 1) 수동 확정 그룹 (러닝 헤더·가사·판번호·워터마크로 이미 확실한 것)
MANUAL = {
 "Soranji": [7,243,251,29,177,308,205,135],
 "Love Story (Richard Clayderman)": [10,237,254],
 "Bella Ciao": [209,277,171],
 "A Thousand Years": [299,313,58,163,318,311,172],
 "In the End": [207,190,227,303],
 "Despacito": [45,76,279,30,110],
 "La Campanella (Liszt)": [103,249,115,264,39,222,73,1],
 "Chopin Etude Op.10 No.4": [44,184,291,233,41,27],
 "Chopin Etude Op.25 No.1": [31,245,20,11],
 "Waltz of the Flowers (Tchaikovsky)": [234,161,154],
 "Perfect (Ed Sheeran)": [226,231],
 "Fly Me To The Moon": [191,314,71],
 "Someone You Loved": [60,310,74],
 "Kiss The Rain": [181,54,273],
 "Beautiful In White (vuca)": [193,223,289],
 "Eyes Of Love": [258,139,189],
 "Em (Binz ft. Soobin)": [286,168,72,3,137,102],
 "Mariage d'Amour (solfege)": [208,86,174,155,296,122,248,287,88,315,111,140,113],
 "La Maritza (solfege)": [302,312,194,280,212],
 "Proud of You (solfege)": [59,69,305,241],
 "Windy Hill": [239,165],
 "He's a Pirate": [138,14,324],
 "Icarus (Tony Ann)": [255,42],
 "A Comme Amour": [106,186,126],
 "Chia Xa": [66,47],
 "Illusionary Daytime": [229,61],
 "Golden Hour": [143,146,282,53,188],
 "Di Vang Nhat Nhoa": [178,2,320,108,319],
}
used = {i for v in MANUAL.values() for i in v}

# 2) 남은 제목 페이지를 (w,h) 버킷 안에서 자동 확장
bucket = collections.defaultdict(list)
for i, p in P.items():
    if i not in used:
        bucket[(p["w"], p["h"])].append(i)

def keyof(n):
    m = re.search(r'\b(\d)([#b])\b', n)
    if m: return m.group(1)+m.group(2)
    if re.search(r'(?<![A-Za-z])C(?![A-Za-z#b])', n): return 'C'
    return None

for i,p in P.items():
    p["key"] = keyof(p["note"])

auto = {}
for i, p in sorted(P.items()):
    if i in used or not p["title"]:
        continue
    grp, last_meas, want = [i], 0, 2
    pool = sorted(x for x in bucket[(p["w"], p["h"])] if x != i)
    cur_key, cur_wm = p["key"], p["wm"]
    while True:
        cands = [x for x in pool
                 if x not in used and P[x]["page"] == want
                 and P[x]["meas"] is not None and P[x]["meas"] > last_meas]
        if not cands:
            break
        def score(x):
            q = P[x]; s = 0
            if cur_key and q["key"] == cur_key: s += 3
            if cur_wm and q["wm"] == cur_wm: s += 3
            if q["wm"] and not cur_wm: s -= 1
            gap = q["meas"] - last_meas
            s += 2 if 8 <= gap <= 40 else 0
            return s
        cands.sort(key=score, reverse=True)
        best = cands[0]
        if score(best) < 3:
            break
        if len(cands) > 1 and score(cands[1]) == score(best):
            break                       # 동점이면 애매하므로 중단
        grp.append(best); used.add(best)
        last_meas = P[best]["meas"]; cur_key = P[best]["key"] or cur_key
        cur_wm = P[best]["wm"] or cur_wm
        want += 1
    used.add(i)
    auto[p["title"]] = grp

review = sorted(i for i in P if i not in used)
out = {"manual": MANUAL, "auto": auto, "review": review}
json.dump(out, open('tools/batch2/groups.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

multi = {k: v for k, v in auto.items() if len(v) > 1}
print(f"수동 확정 {len(MANUAL)}곡 / {sum(len(v) for v in MANUAL.values())}장")
print(f"자동 확장 {len(auto)}곡 / {sum(len(v) for v in auto.values())}장  (그중 2장 이상 {len(multi)}곡)")
print(f"미배정(확인필요) {len(review)}장\n")
for k, v in sorted(multi.items(), key=lambda kv: -len(kv[1])):
    print(f"  {len(v)}장  {k}")
