#!/usr/bin/env python3
"""미분류 34장을 '같은 곡으로 보이는 묶음'으로 쪼개 별도 항목으로 만든다.

사이트에서 묶음별로 넘겨보고 곡명을 알려주면 그대로 편입할 수 있다.
"""
import json, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'raw', 'added')
DATA = os.path.join(ROOT, 'data')
OLD = os.path.join(DATA, '_미분류 (batch2)')
idx = json.load(open(f'{ROOT}/tools/batch2/index.json'))
notes = {}
for line in open(f'{ROOT}/tools/batch2/notes.md', encoding='utf-8'):
    m = re.match(r'^(\d+)\s+(.*)$', line.rstrip())
    if m: notes[int(m.group(1))] = m.group(2)

# 같은 곡으로 보이는 묶음 — 마디 번호가 이어지고 조표·기보 스타일이 일치
CLUSTERS = [
 ("A", "C장조 무궁동 16분음표",      [304, 117, 48, 272], "p2 m16 · p3 m29 · p4 m41 · p6 m73 — 양손 16분음표가 쉬지 않고 흐르는 편곡"),
 ("B", "3♭ 페달 위주 서정곡",         [204, 218],          "p2 m17 · p3 m37(끝) — 마디마다 Ped., 페르마타로 종료"),
 ("C", "3♭ 액센트 오스티나토",        [281, 263, 185, 62], "p3 m27 · p4 m40 · p5 m50 · p6 m66 — 워터마크 @piano23.5"),
 ("D", "고전 소품 (Fine / D.C.)",     [9, 224],            "m44에 Fine, m75에 D.C. al Fine — 3# 장식음(tr) 포함"),
 ("E", "고전 대곡 (트리플렛)",        [210, 100],          "p4 m105 · p5 m138 — 140마디가 넘는 긴 곡, tr·셋잇단음표"),
 ("F", "3♭→4♭ 소품",                 [15, 297],           "p2 m21 · p3 m44(끝) — 마지막 장에 'no pedal'"),
 ("G", "1♭ 곡",                       [232, 288],          "p3 m62 · p4 m72 — ff 클라이맥스"),
]
SINGLES = [35, 63, 65, 70, 85, 131, 149, 150, 156, 236, 276, 278, 285, 292, 301, 321]


def main():
    meta = json.load(open(f'{ROOT}/tools/pieces.json', encoding='utf-8'))
    meta['pieces'] = [p for p in meta['pieces'] if p['id'] != 'unsorted-batch2']
    if os.path.isdir(OLD): shutil.rmtree(OLD)

    lines = ["# 미확인 페이지\n",
             "곡명을 아시면 아래 빈칸에 적어주세요. 그대로 `data/` 로 편입합니다.\n"]
    for tag, desc, ids, hint in CLUSTERS:
        folder = f"_미확인 {tag} · {desc}"
        d = os.path.join(DATA, folder)
        os.makedirs(d, exist_ok=True)
        for n, i in enumerate(ids, 1):
            shutil.copy2(os.path.join(SRC, idx[str(i)]), os.path.join(d, f"p{n}.JPEG"))
        meta['pieces'].append({
            "dir": folder, "id": f"unknown-{tag.lower()}",
            "title": f"미확인 {tag} · {desc}", "composer": f"{len(ids)}장 — 곡명 미상",
            "note": hint, "tags": ["미확인"],
        })
        lines.append(f"\n## 미확인 {tag} — {desc} ({len(ids)}장)\n\n{hint}\n\n- 곡명: \n")
        for i in ids:
            lines.append(f"  - `#{i}` {notes.get(i,'')}\n")

    folder = "_미확인 낱장"
    d = os.path.join(DATA, folder)
    os.makedirs(d, exist_ok=True)
    for n, i in enumerate(SINGLES, 1):
        shutil.copy2(os.path.join(SRC, idx[str(i)]), os.path.join(d, f"p{n:02d}.JPEG"))
    meta['pieces'].append({
        "dir": folder, "id": "unknown-singles",
        "title": "미확인 · 낱장 모음", "composer": f"{len(SINGLES)}장 — 각각 다른 곡",
        "note": "같은 곡으로 묶을 짝을 못 찾은 페이지들. 한 장씩 서로 다른 곡일 가능성이 큽니다",
        "tags": ["미확인"],
    })
    lines.append(f"\n## 미확인 · 낱장 모음 ({len(SINGLES)}장)\n\n각 장이 서로 다른 곡으로 보입니다.\n\n")
    for n, i in enumerate(SINGLES, 1):
        lines.append(f"- `p{n:02d}` (`#{i}`) {notes.get(i,'')} — 곡명: \n")

    json.dump(meta, open(f'{ROOT}/tools/pieces.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    open(f'{ROOT}/tools/pieces.json', 'a').write("\n")
    open(f'{ROOT}/docs/unidentified.md', 'w', encoding='utf-8').writelines(lines)
    print(f"묶음 {len(CLUSTERS)}개 + 낱장 {len(SINGLES)}장 → data/ 에 {len(CLUSTERS)+1}개 항목")
    print("체크리스트: docs/unidentified.md")


if __name__ == '__main__':
    main()
