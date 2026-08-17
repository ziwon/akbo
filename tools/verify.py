#!/usr/bin/env python3
"""data/ 무결성 검사 — 빌드 전에 돌린다.

  1. raw/ 의 모든 원본이 data/ 어딘가에 있는가 (유실 검사)
  2. data/ 폴더명이 pieces.json 과 일치하는가
  3. id 중복, 폴더명에 경로 구분자 포함 여부
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, RAW = os.path.join(ROOT, 'data'), os.path.join(ROOT, 'raw')


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()


def walk(root):
    for dp, _, fs in os.walk(root):
        for f in fs:
            if f.lower().endswith(('.jpeg', '.jpg', '.png')):
                yield os.path.join(dp, f)


def main():
    bad = []
    in_data = {md5(p): p for p in walk(DATA)}
    orphan = [p for p in walk(RAW) if md5(p) not in in_data]
    if orphan:
        bad.append(f"raw/ 에만 있고 data/ 에 없는 원본 {len(orphan)}장")
        for p in orphan[:10]: bad.append(f"    {os.path.relpath(p, ROOT)}")

    meta = json.load(open(os.path.join(ROOT, 'tools', 'pieces.json'), encoding='utf-8'))
    ids = [p['id'] for p in meta['pieces']]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup: bad.append(f"id 중복: {dup}")

    for p in meta['pieces']:
        if '/' in p['dir'] or '\\' in p['dir']:
            bad.append(f"폴더명에 경로 구분자: {p['dir']!r}")
        if not os.path.isdir(os.path.join(DATA, p['dir'])):
            bad.append(f"폴더 없음: {p['dir']!r} (id={p['id']})")

    known = {p['dir'] for p in meta['pieces']}
    for d in os.listdir(DATA):
        if os.path.isdir(os.path.join(DATA, d)) and d not in known:
            bad.append(f"pieces.json 에 없는 폴더: {d!r}")

    if bad:
        print("문제 발견:"); [print("  " + b) for b in bad]; sys.exit(1)
    n = len(in_data)
    print(f"이상 없음 — data/ {n}장, 원본 전부 포함, id·폴더 일치")


if __name__ == '__main__':
    main()
