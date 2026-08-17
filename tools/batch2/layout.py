#!/usr/bin/env python3
"""페이지 레이아웃 지문.

같은 PDF 에서 나온 페이지는 오선 간격·좌우 여백·단 수가 거의 같다.
크기(w,h) 만으로는 안 갈리는 큰 버킷을 이 지문으로 다시 쪼갠다.

  staff : 오선 5줄의 줄 간격 (px, 폭으로 정규화)
  L,R   : 내용이 시작/끝나는 x 위치 (폭 대비 비율)
  sys   : 시스템(단) 개수
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def signature(path):
    with Image.open(path) as im:
        g = im.convert("L")
        W0, H0 = g.size
        # 폭 1000 기준으로 정규화해 서로 다른 캡처 배율을 흡수
        s = 1000 / W0
        g = g.resize((1000, max(1, int(H0 * s))), Image.LANCZOS)
        a = np.asarray(g, dtype=np.uint8)
    dark = a < 160
    rows = dark.sum(1).astype(float)
    cols = dark.sum(0).astype(float)

    # 좌우 여백: 열 방향으로 잉크가 있는 구간
    thr_c = max(2.0, cols.max() * 0.04)
    on = np.where(cols > thr_c)[0]
    L = float(on[0]) / 1000 if len(on) else 0.0
    R = float(on[-1]) / 1000 if len(on) else 1.0

    # 시스템: 행 방향 잉크 밀도가 높은 구간의 덩어리 수
    thr_r = max(3.0, rows.max() * 0.25)
    band = rows > thr_r
    sysn = int(np.sum(band[1:] & ~band[:-1])) + (1 if band[0] else 0)

    # 오선 간격: 잉크가 가장 진한 구간에서 행 자기상관의 첫 봉우리
    staff = 0.0
    if band.any():
        seg = rows[band.argmax(): band.argmax() + 220]
        if len(seg) > 40:
            seg = seg - seg.mean()
            ac = np.correlate(seg, seg, "full")[len(seg) - 1:]
            if ac[0] > 0:
                ac = ac / ac[0]
                lo, hi = 4, min(40, len(ac) - 1)
                if hi > lo:
                    staff = float(lo + int(np.argmax(ac[lo:hi])))
    return dict(L=round(L, 4), R=round(R, 4), sys=sysn, staff=round(staff, 2))


def sig_of_index(i):
    idx = json.load(open(f'{ROOT}/tools/batch2/index.json'))
    return signature(os.path.join(ROOT, 'raw', 'added', idx[str(i)]))


if __name__ == '__main__':
    # 정답을 아는 그룹으로 검증
    groups = json.load(open(f'{ROOT}/tools/batch2/groups.json', encoding='utf-8'))
    for name in ["Soranji", "A Thousand Years", "Em (Binz ft. Soobin)",
                 "Chopin Etude Op.10 No.4", "Despacito"]:
        ids = groups['manual'][name]
        print(f"\n■ {name}")
        for i in ids:
            s = sig_of_index(i)
            print(f"   #{i:<4} L={s['L']:.3f} R={s['R']:.3f} sys={s['sys']:<2} staff={s['staff']}")
