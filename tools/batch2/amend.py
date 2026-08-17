#!/usr/bin/env python3
"""미분류 페이지를 확정된 곡 폴더로 옮긴다.

ASSIGN 의 각 항목은 (pieces.json 의 id, [판독 인덱스 …]) 이며
인덱스 순서가 곧 p1, p2, … 순서다. 이미 폴더에 있는 페이지는 건너뛴다.
"""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "raw", "added")
DATA = os.path.join(ROOT, "data")
UNS = os.path.join(DATA, "_미분류 (batch2)")
idx = json.load(open(f'{ROOT}/tools/batch2/index.json'))
meta = json.load(open(f'{ROOT}/tools/pieces.json', encoding='utf-8'))
dir_of = {p['id']: p['dir'] for p in meta['pieces']}

ASSIGN = [
 ("every-breath-you-take",      [105, 147, 46, 119, 230]),
 ("radetzky-march",             [306, 17]),
 ("farewell-of-slavianka",      [129, 202, 83]),
 ("je-te-laisserai-des-mots",   [109, 246, 132]),
 ("et-si-tu-n-existais-pas",    [8, 56]),
 ("seasons-by-wave-to-earth",   [195, 34]),
]

def main():
    moved = 0
    for pid, ids in ASSIGN:
        d = os.path.join(DATA, dir_of[pid])
        if not os.path.isdir(d):
            print(f"  ! 폴더 없음: {pid}"); continue
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        for n, i in enumerate(ids, 1):
            shutil.copy2(os.path.join(SRC, idx[str(i)]), os.path.join(d, f"p{n}.JPEG"))
        for i in ids:
            u = os.path.join(UNS, f"p{i:03d}.JPEG")
            if os.path.exists(u):
                os.remove(u); moved += 1
    left = len([f for f in os.listdir(UNS) if f.endswith('.JPEG')])
    print(f"{len(ASSIGN)}곡 갱신, 미분류에서 {moved}장 이동 → 남은 미분류 {left}장")

if __name__ == '__main__':
    main()
