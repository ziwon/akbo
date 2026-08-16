#!/usr/bin/env python3
"""각 곡의 참고 영상 후보를 YouTube에서 검색해 JSON으로 뽑습니다 (API 키 불필요).
   결과는 사람이 골라 tools/pieces.json 의 youtube 필드에 넣습니다."""
import json, os, subprocess, sys, concurrent.futures as cf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "tools", "pieces.json")
OUT = os.path.join(ROOT, "tools", "yt_candidates.json")
N = int(os.environ.get("YT_N", "4"))

# 검색어를 자동 생성하면 편곡·커버가 섞여 나오는 곡이 많아 곡별로 명시한다.
QUERIES = {
    "50-nam-ve-sau": "50 Năm Về Sau Đặng Thanh Tuyền",
    "always-with-me": "いつも何度でも 木村弓 千と千尋の神隠し",
    "atlantis": "Imperio Atlantis",
    "beanie": "Chezile Beanie",
    "beautiful-in-white-canon-in-d": "Shane Filan Beautiful In White",
    "comptine-dun-autre-ete": "Yann Tiersen Comptine d'un autre été l'après-midi",
    "congratulations": "Mac Miller Congratulations feat Bilal",
    "dance-of-the-little-swans": "Tchaikovsky Dance of the Little Swans Swan Lake",
    "dao-buoc-hongkong-1999": "漫步香港1999 钢琴",
    "feeling-good": "Muse Feeling Good",
    "idea-15": "Gibran Alcocer Idea 15",
    "la-maritza": "Sylvie Vartan La Maritza",
    "la-tartine-de-beurre": "La tartine de beurre Das Butterbrot Mozart KV Anh 284n",
    "little-things": "ANBR Little Things piano",
    "menuett-g-moll": "Handel Menuett g-moll Kempff",
    "noctilune-no-1": "Carlo Constantini Noctilune",
    "chopin-nocturne-op9-no1": "Chopin Nocturne Op. 9 No. 1 B flat minor",
    "nu-pogodi-the-urn": "Ну погоди музыка из 1 выпуска урна",
    "once-upon-a-december": "Anastasia Once Upon a December",
    "sibelius-op76-no2": "Sibelius 13 Pieces Op. 76 No. 2 Etude piano",
    "passacaglia": "Handel Halvorsen Passacaglia piano",
    "passacaglia-chords": "Handel Halvorsen Passacaglia piano",
    "por-una-cabeza": "Carlos Gardel Por una Cabeza",
    "por-una-cabeza-alt": "Carlos Gardel Por una Cabeza",
    "chopin-prelude-op28-no4": "Chopin Prelude Op. 28 No. 4 E minor",
    "reason": "Yiruma Reason",
    "sayonara-no-natsu": "さよならの夏 コクリコ坂から 手嶌葵",
    "secret-duet": "不能說的秘密 鬥琴 piano battle",
    "secret-solo": "周杰倫 Secret 不能說的秘密 piano",
    "tada-koe-hitotsu": "ロクデナシ ただ声一つ",
    "the-magic-of-love": "The Magic of Love piano",
    "seasons-june-barcarolle": "Tchaikovsky The Seasons June Barcarolle",
    "tiec-tra-sao": "星茶会 钢琴",
    "time-travel-theme": "不能說的秘密 Secret 周杰倫 時光機",
    "track-in-time": "Track in Time piano",
    "shostakovich-waltz-no2": "Shostakovich Waltz No. 2 Jazz Suite",
    "chopin-waltz-a-minor-b150": "Chopin Waltz in A minor B 150",
    "chopin-waltz-op69-no1": "Chopin Waltz Op. 69 No. 1 A flat major L'adieu",
    "yesterday-once-more": "Carpenters Yesterday Once More",
}


def search(pid, q):
    try:
        r = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--no-warnings", "-J", f"ytsearch{N}:{q}"],
            capture_output=True, text=True, timeout=90)
        entries = json.loads(r.stdout).get("entries", []) if r.stdout else []
    except Exception as e:
        return pid, {"query": q, "error": str(e)[:120], "results": []}
    out = [{
        "id": e.get("id"),
        "title": (e.get("title") or "")[:110],
        "channel": e.get("channel") or e.get("uploader") or "",
        "duration": e.get("duration"),
        "views": e.get("view_count"),
    } for e in entries if e.get("id")]
    return pid, {"query": q, "results": out}


def main():
    meta = json.load(open(META, encoding="utf-8"))
    ids = [p["id"] for p in meta["pieces"]]
    missing = [i for i in ids if i not in QUERIES]
    if missing:
        print("! 검색어 없는 곡:", missing, file=sys.stderr)

    out = {}
    with cf.ThreadPoolExecutor(6) as ex:
        futs = [ex.submit(search, i, QUERIES[i]) for i in ids if i in QUERIES]
        for n, f in enumerate(cf.as_completed(futs), 1):
            pid, res = f.result()
            out[pid] = res
            print(f"  [{n}/{len(futs)}] {pid}: {len(res['results'])}건", file=sys.stderr)

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{len(out)}곡 -> {OUT}")


if __name__ == "__main__":
    main()
