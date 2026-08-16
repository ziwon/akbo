# Obsidian 연동 검토

akbo에 Obsidian을 어떻게 끼워 넣을지, 그리고 [FlareGraph](https://github.com/ziwon/FlareGraph)
구조를 얼마나 참고할지에 대한 검토 메모.

## 결론

**철학은 그대로 빌리고, 스택은 빌리지 않는다.**

FlareGraph의 핵심 주장은 *Obsidian은 사람의 인터페이스로 두고, 파생물은 전부 빌드로 만든다*
이다. akbo는 이미 같은 모양이다.

```
FlareGraph:  Vault(.md) → R2 → Indexer → D1/Vectorize → MCP/API
akbo:        data/ + pieces.json → build.py → site/
```

바꿀 지점은 하나. `tools/pieces.json`(손으로 고치는 JSON 덩어리)을 **곡당 마크다운 1개**로
옮기면 Obsidian이 그대로 편집기가 된다.

## 제안하는 구조

```markdown
vault/Scores/Chopin - Nocturne Op.9 No.1.md
---
akbo_id: chopin-nocturne-op9-no1
dir: "Nocturne Op.9 No.1 (Chopin)"
title: Nocturne in B♭ minor, Op. 9 No. 1
composer: Frédéric Chopin
key: B♭ minor
tempo: 116
status: 연습중
tags: [piano/classical, romantic]
---

## 연습 노트
- 2026-08-16 — 3p m43 왼손 아르페지오, 손목 회전으로. [[페달 노트]]
- 목표 ♩=116, 현재 92
```

`build.py`가 JSON 대신 프론트매터를 읽고, 본문(연습 노트)은 뷰어 사이드 패널로 함께 내보낸다.

### 얻는 것

| | |
|---|---|
| **연습 저널** | 지금 akbo에 완전히 없는 기능. 데일리 노트와 자연스럽게 엮인다 |
| **메타데이터 편집성** | JSON 39개 블록 대신 Obsidian 속성 UI |
| **백링크·그래프** | "루바토", "왼손 도약" 같은 개념 노트로 곡들이 묶인다 |

## 빌리지 않을 것: 인프라

FlareGraph는 R2 + Queues + D1(FTS5) + Vectorize(BGE-M3) + MCP Worker다. 노트가 수천 개고
에이전트가 인용을 붙여 검색해야 할 때 값을 한다.

akbo는 **39곡, `library.json` 18KB**다. 이미 브라우저에 통째로 올라가 즉시 검색된다.
여기에 임베딩·벡터 검색을 얹는 건 오버엔지니어링이고 유지보수 비용만 남는다.

### FlareGraph를 실제로 붙일 시점

- 곡 수가 수백 개로 늘고
- "왼손이 약점이라고 적어둔 곡 뽑아줘" 같은 걸 에이전트에게 시키고 싶을 때

그때는 akbo vault를 FlareGraph의 인덱싱 대상 폴더로 얹기만 하면 된다.
**지금 구조를 그대로 두면 그 길이 막히지 않는다.**

## 백업과의 접점

`data/` 39MB가 이 머신에만 있는 문제는 FlareGraph 없이 해결하는 게 낫다.
R2 버킷 하나에 rclone / `wrangler r2 object put` 으로 미러하면 끝이고, Cloudflare 계정은 이미 있다.

## 진행 순서

1. **A. 프론트매터 전환** — `pieces.json` → `vault/Scores/*.md` 39개 + `build.py` 파서 교체
2. **B. 연습 노트 뷰어 노출** — A + 뷰어 사이드 패널
3. **C. 백업** — R2 미러 스크립트 (A/B와 독립적으로 언제든)

A만 해도 Obsidian에서 곡 목록이 살아나고, 되돌리기도 쉽다. A → 써보고 → B 순서를 권한다.
