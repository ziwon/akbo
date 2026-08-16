# akbo

아이패드·PC에서 보는 피아노 악보 뷰어 — <https://akbo.pages.dev>

정적 사이트라 빌드 서버가 필요 없습니다.

> **저장소에는 악보 이미지가 없습니다.** 저작권 때문에 `raw/`·`data/`와 빌드 산출물
> (`site/scores/`, `site/library.json`)을 제외했습니다. 클론만으로는 빌드가 되지 않으며,
> 로컬 `data/`(곡별 폴더 구조)를 그대로 두고 빌드해야 합니다. 악보 원본은 별도로 백업하세요.

```
raw/      원본 스크린샷 121장 (UUID 파일명, 손대지 않음)
data/     곡별 39개 폴더 · p1.JPEG, p2.JPEG …  ← 편집은 여기서
tools/    pieces.json(메타데이터) · build.py · make_icons.py
site/     배포되는 정적 사이트 (빌드 산출물)
```

## 빌드

```bash
python3 tools/build.py          # 변경분만 WebP 변환 + library.json 생성
python3 tools/build.py --force  # 전부 다시 변환
```

`data/`의 JPEG을 WebP(q82)로 변환해 `site/scores/<id>/`에 넣고, 목록 데이터인
`site/library.json`을 만듭니다. 121페이지 39MB → 12MB.

곡 제목·작곡가·태그는 **`tools/pieces.json`** 에서 고칩니다. `dir`은 `data/` 폴더명,
`id`는 URL 슬러그(바꾸면 링크와 저장된 진도가 끊깁니다).

## 로컬 확인

```bash
python3 -m http.server 8788 -d site
# http://127.0.0.1:8788
```

## 배포 (Cloudflare Pages)

```bash
wrangler pages deploy site --project-name score-leaf
```

첫 배포 때 프로젝트가 없으면 생성 여부를 묻습니다. 이후 `score-leaf.pages.dev`.

`site/_headers`가 캐시 정책을 담당합니다 — 악보 이미지는 1년 immutable,
`library.json`과 `sw.js`는 매번 재검증(새 배포가 바로 반영).

> GitHub Pages로 옮기려면 `site/`를 그대로 올리면 됩니다. 모든 경로가 상대경로라
> `ziwon.github.io/score-leaf` 같은 서브패스에서도 그대로 동작합니다.

## 조작

| | |
|---|---|
| 페이지 넘김 | 화면 좌·우 탭, 좌우 스와이프, `←` `→` `Space` `PageUp/Down` |
| UI 숨김/표시 | 화면 가운데 탭 |
| 두 장 보기 | `S` (가로 화면 + 700px 이상에서 동작) |
| 폭 맞춤 | `W` |
| 전체화면 | `F` |
| 목록으로 | `Esc` |
| 검색 | 목록에서 `/` |

즐겨찾기·마지막으로 본 페이지·테마는 브라우저에 저장됩니다.
목록 우측 상단 ↓ 버튼을 누르면 전체 악보를 캐시에 담아 **인터넷 없이도** 열립니다.
아이패드에서는 Safari 공유 → "홈 화면에 추가"로 앱처럼 쓸 수 있습니다.

## 주의

쇼팽·차이콥스키·헨델·시벨리우스를 뺀 나머지는 저작권이 살아있는 곡입니다.
`.pages.dev`는 기본이 공개 URL이므로, 비공개로 두려면 Cloudflare Access
(Zero Trust → Access → Applications)를 앞에 걸어 지정한 이메일만 열도록 설정하세요.
