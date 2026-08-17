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

# 2차 배치 검색어 (한글·베트남어 제목은 자동 생성이 안 되므로 명시)
QUERIES.update({
 "soranji":"Mrs. GREEN APPLE ソランジ Soranji",
 "love-story-richard-clayderman":"Richard Clayderman Love Story",
 "bella-ciao":"Bella Ciao La Casa de Papel",
 "a-thousand-years":"Christina Perri A Thousand Years",
 "in-the-end":"Linkin Park In The End",
 "despacito":"Luis Fonsi Despacito ft Daddy Yankee",
 "la-campanella-liszt":"Liszt La Campanella piano",
 "chopin-etude-op-10-no-4":"Chopin Etude Op 10 No 4 Torrent",
 "chopin-etude-op-25-no-1":"Chopin Etude Op 25 No 1 Aeolian Harp",
 "waltz-of-the-flowers-tchaikovsky":"Tchaikovsky Waltz of the Flowers Nutcracker",
 "perfect-ed-sheeran":"Ed Sheeran Perfect",
 "fly-me-to-the-moon":"Frank Sinatra Fly Me To The Moon",
 "someone-you-loved":"Lewis Capaldi Someone You Loved",
 "kiss-the-rain":"Yiruma Kiss The Rain",
 "beautiful-in-white-vuca":"Shane Filan Beautiful In White",
 "eyes-of-love":"Eyes Of Love Mauri Direc piano",
 "em-binz-ft-soobin":"Binz Em ft Soobin",
 "mariage-d-amour-solfege":"Paul de Senneville Mariage d'Amour",
 "la-maritza-solfege":"Sylvie Vartan La Maritza",
 "proud-of-you-solfege":"Fiona Fung Proud of You",
 "windy-hill":"久石譲 風の丘 魔女の宅急便",
 "he-s-a-pirate":"He's a Pirate Pirates of the Caribbean Klaus Badelt",
 "icarus-tony-ann":"Tony Ann Icarus",
 "a-comme-amour":"Richard Clayderman A Comme Amour",
 "chia-xa":"還珠格格 主題曲 鋼琴",
 "illusionary-daytime":"Shirfine 幻昼 Illusionary Daytime",
 "golden-hour":"JVKE Golden Hour",
 "di-vang-nhat-nhoa":"Dĩ Vãng Nhạt Nhòa",
 "solas":"Jamie Duffy Solas",
 "comptine-d-un-autre-ete-l-apres-midi":"Yann Tiersen Comptine d'un autre été l'après-midi",
 "a-town-with-an-ocean-view":"久石譲 海の見える街 魔女の宅急便",
 "et-si-tu-n-existais-pas":"Joe Dassin Et si tu n'existais pas",
 "the-scientist":"Coldplay The Scientist",
 "samsung-alarm-homecoming":"Samsung Galaxy Homecoming alarm ringtone",
 "the-interstellar-experience":"Tony Ann Interstellar Experience",
 "musette-in-d-bwv-126":"Bach Musette in D major BWV Anh 126",
 "hit-the-road-jack":"Ray Charles Hit The Road Jack",
 "pulse-a-k-a-my-neighbour-s-car-alarm":"Tony Ann Pulse",
 "czardas":"Monti Csardas violin",
 "chopin-valse-no-19-in-a-mineur":"Chopin Waltz in A minor B 150",
 "endless-love-the-mythe":"神話 The Myth Endless Love Jackie Chan Kim Hee sun",
 "chopin-waltz-op-64-improvisation":"不能說的秘密 蕭邦圓舞曲 鬥琴",
 "moonlight":"しがない高校生 Moonlight piano",
 "piano-sonata-no-16-k-545-2nd-mvt":"Mozart Sonata K 545 second movement Andante",
 "akaza-s-love-theme":"鬼滅の刃 無限城編 猗窩座 恋雪 テーマ",
 "see-you-again":"Wiz Khalifa See You Again ft Charlie Puth",
 "cry-for-me":"Michita Cry For Me",
 "a-thousand-miles":"Vanessa Carlton A Thousand Miles",
 "from-the-beginning-until-now":"겨울연가 처음부터 지금까지",
 "every-breath-you-take":"The Police Every Breath You Take",
 "je-te-laisserai-des-mots":"Patrick Watson Je te laisserai des mots",
 "tori-no-uta-short":"Lia 鳥の詩 AIR",
 "xing-cha-hui-2":"灰澈 星茶会",
 "czerny-op-599-no-30":"Czerny Op 599 No 30 piano",
 "drowning-love-chasing-kou":"Antonis Paterakis Drowning love Chasing Kou piano",
 "married-life-theme-from-up":"Michael Giacchino Married Life Up",
 "farewell-of-slavianka":"Прощание славянки Farewell of Slavianka",
 "habanera":"Bizet Carmen Habanera",
 "my-love":"Westlife My Love",
 "piano-sonata-no-16-k-545-3rd-mvt":"Mozart Sonata K 545 third movement Rondo Allegretto",
 "dong-mien":"Đông Miên piano",
 "detective-conan-main-theme":"名探偵コナン メインテーマ 大野克夫",
 "hungarian-dance-no-5-in-g-minor":"Brahms Hungarian Dance No 5",
 "sinking-town-tentententen":"倉橋ヨエコ sinking town",
 "my-lie-your-lie-in-april":"四月は君の嘘 My Lie 横山克",
 "he-s-a-pirate-easy-version":"He's a Pirate piano easy",
 "l-s-theme":"Death Note L's Theme",
 "from-the-start-beginner-piano-adaptation":"Laufey From The Start",
 "mariage-d-amour":"Paul de Senneville Mariage d'Amour",
 "a-time-for-us-romeo-juliet":"Nino Rota A Time For Us Romeo and Juliet",
 "seasons-by-wave-to-earth":"wave to earth seasons",
 "noi-phao-hoa-ruc-ro-i-e-tro-ve-8":"Nơi Pháo Hoa Rực Rỡ Orange Hoàng Dũng",
 "wedding-march":"Mendelssohn Wedding March Midsummer Night's Dream",
 "beanie-2":"Chezile Beanie",
 "flower-dance-c-major-simplified":"DJ Okawari Flower Dance",
 "a-little-story":"Valentin A Little Story piano",
 "the-5th-melody-of-the-night":"夜的第五樂章 鋼琴",
 "a-million-dream":"The Greatest Showman A Million Dreams",
 "never-be-alone-fnaf-4":"Shadrow Never Be Alone FNAF 4",
 "yume-to-hazakura":"夢と葉桜 初音ミク 青木月光",
 "komorebi":"m-taku Komorebi piano",
 "right-here-waiting-for-you":"Richard Marx Right Here Waiting",
 "a-little-sweet":"汪蘇瀧 有點甜",
 "farewell-letter":"訣別書 鋼琴",
 "radetzky-march":"Johann Strauss Radetzky March",
 "hazy-moon":"Astarte Chrono Hazy Moon piano",
 "10-ngan-nam":"10 Ngàn Năm piano",
 "flower-day":"꽃날 Flower Day piano",
})

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
    ids = [p["id"] for p in meta["pieces"] if not p.get("youtube")]
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
