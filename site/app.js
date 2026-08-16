/* score-leaf — 악보 뷰어 */
(() => {
'use strict';

const $ = (id) => document.getElementById(id);
const LS = {
  get(k, d) { try { return JSON.parse(localStorage.getItem('sl:' + k)) ?? d; } catch { return d; } },
  set(k, v) { try { localStorage.setItem('sl:' + k, JSON.stringify(v)); } catch {} },
};

let LIB = { pieces: [] };
let byId = new Map();
let favs = new Set(LS.get('favs', []));
let progress = LS.get('progress', {});   // id -> 마지막으로 본 페이지 index
let recent = LS.get('recent', []);       // 최근 연 id (앞이 최신)
let filter = 'all';
let query = '';

/* ══════════════ 테마 ══════════════ */
const themeBtn = $('themeBtn');
function applyTheme(t) {
  if (t) document.documentElement.setAttribute('data-theme', t);
  else document.documentElement.removeAttribute('data-theme');
  const dark = t === 'dark' || (!t && matchMedia('(prefers-color-scheme:dark)').matches);
  document.querySelector('meta[name=theme-color]').content = dark ? '#12141a' : '#f6f4ef';
}
applyTheme(LS.get('theme', null));
themeBtn.addEventListener('click', () => {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : cur === 'light' ? null : 'dark';
  LS.set('theme', next); applyTheme(next);
});

/* ══════════════ 토스트 ══════════════ */
let toastTimer;
function toast(msg, ms = 2400) {
  const el = $('toast');
  el.textContent = msg; el.hidden = false;
  clearTimeout(toastTimer);
  if (ms) toastTimer = setTimeout(() => { el.hidden = true; }, ms);
}

/* ══════════════ 라이브러리 ══════════════ */
function tagList() {
  const counts = new Map();
  for (const p of LIB.pieces) for (const t of p.tags || []) counts.set(t, (counts.get(t) || 0) + 1);
  return [...counts.entries()].filter(([, n]) => n >= 2).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).map(([t]) => t);
}

function renderFilters() {
  const base = [['all', '전체'], ['fav', '★ 즐겨찾기'], ['recent', '최근']];
  const chips = [...base, ...tagList().map(t => ['tag:' + t, t])];
  $('filters').replaceChildren(...chips.map(([key, label]) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'chip'; b.textContent = label;
    b.setAttribute('aria-pressed', String(filter === key));
    b.addEventListener('click', () => { filter = key; renderFilters(); renderGrid(); });
    return b;
  }));
}

function visiblePieces() {
  let list = LIB.pieces;
  if (filter === 'fav') list = list.filter(p => favs.has(p.id));
  else if (filter === 'recent') list = recent.map(id => byId.get(id)).filter(Boolean);
  else if (filter.startsWith('tag:')) { const t = filter.slice(4); list = list.filter(p => (p.tags || []).includes(t)); }
  if (query) {
    const q = query.toLowerCase();
    list = list.filter(p => (p.title + ' ' + p.composer + ' ' + p.note + ' ' + (p.tags || []).join(' ')).toLowerCase().includes(q));
  }
  return list;
}

/** "—" 같은 자리표시자는 부제에서 빼고, 없으면 편곡 메모로 대체 */
const clean = (s) => (s && s.trim() !== '—' ? s.trim() : '');
const subtitle = (p) => clean(p.composer) || clean(p.note);

function renderGrid() {
  const list = visiblePieces();
  const frag = document.createDocumentFragment();

  for (const p of list) {
    const card = document.createElement('a');
    card.className = 'card'; card.href = '#/p/' + p.id;

    const thumb = document.createElement('div');
    thumb.className = 'thumb';

    const img = new Image();
    img.src = p.cover.src; img.alt = ''; img.loading = 'lazy'; img.decoding = 'async';
    img.width = p.cover.w; img.height = p.cover.h;
    thumb.append(img);

    const star = document.createElement('button');
    star.type = 'button'; star.className = 'star'; star.setAttribute('aria-label', '즐겨찾기');
    star.setAttribute('aria-pressed', String(favs.has(p.id)));
    star.innerHTML = '<svg viewBox="0 0 24 24"><path d="m12 3.8 2.5 5.2 5.7.8-4.1 4 1 5.7-5.1-2.7-5.1 2.7 1-5.7-4.1-4 5.7-.8Z"/></svg>';
    star.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); toggleFav(p.id); star.setAttribute('aria-pressed', String(favs.has(p.id))); });
    thumb.append(star);

    if (p.incomplete) {
      const pill = document.createElement('span');
      pill.className = 'pill'; pill.textContent = '뒷장 없음'; pill.title = p.incomplete;
      thumb.append(pill);
    }

    const badge = document.createElement('span');
    badge.className = 'badge'; badge.textContent = p.pages.length + 'p';
    thumb.append(badge);

    const at = progress[p.id] || 0;
    if (at > 0 && p.pages.length > 1) {
      const bar = document.createElement('div');
      bar.className = 'progress';
      bar.innerHTML = `<i style="width:${Math.round((at + 1) / p.pages.length * 100)}%"></i>`;
      thumb.append(bar);
    }

    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.innerHTML = '<b></b><small></small>';
    meta.querySelector('b').textContent = p.title;
    meta.querySelector('small').textContent = subtitle(p);

    card.append(thumb, meta);
    frag.append(card);
  }

  $('grid').replaceChildren(frag);
  $('empty').hidden = list.length > 0;
  $('stat').textContent = `${LIB.pieces.length}곡 · ${LIB.pageCount}페이지`;
}

function toggleFav(id) {
  favs.has(id) ? favs.delete(id) : favs.add(id);
  LS.set('favs', [...favs]);
  if (filter === 'fav') renderGrid();
}

/* 검색 */
$('q').addEventListener('input', (e) => {
  query = e.target.value.trim();
  $('qclear').hidden = !query;
  renderGrid();
});
$('qclear').addEventListener('click', () => { $('q').value = ''; query = ''; $('qclear').hidden = true; renderGrid(); $('q').focus(); });

/* ══════════════ 뷰어 ══════════════ */
const stage = $('stage'), pagesEl = $('pages'), readerEl = $('reader');
let cur = null;          // 현재 곡
let idx = 0;             // 현재 페이지 index
let spread = LS.get('spread', false);
let fitWidth = LS.get('fitWidth', false);
let chromeTimer = null;
let wakeLock = null;

const step = () => (spread && canSpread() ? 2 : 1);
const canSpread = () => innerWidth > innerHeight && innerWidth >= 700;

function openPiece(id, page) {
  const p = byId.get(id);
  if (!p) { location.hash = '#/'; return; }
  cur = p;
  idx = Number.isInteger(page) ? page : (progress[id] || 0);
  idx = Math.max(0, Math.min(idx, p.pages.length - 1));

  $('rTitle').textContent = p.title;
  $('rComposer').textContent = [clean(p.composer), clean(p.note)].filter(Boolean).join(' · ');
  $('favBtn').setAttribute('aria-pressed', String(favs.has(id)));
  $('spreadBtn').setAttribute('aria-pressed', String(spread));
  $('fitBtn').setAttribute('aria-pressed', String(fitWidth));
  $('scrub').max = String(p.pages.length - 1);

  recent = [id, ...recent.filter(x => x !== id)].slice(0, 24);
  LS.set('recent', recent);

  document.title = `${p.title} — akbo`;
  document.documentElement.dataset.view = 'reader';
  $('library').hidden = true; readerEl.hidden = false;
  renderPages(); showChrome(); requestWakeLock();
}

function closePiece() {
  cur = null;
  document.title = 'akbo';
  document.documentElement.dataset.view = 'library';
  readerEl.hidden = true; $('library').hidden = false;
  releaseWakeLock();
  if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
  renderGrid();
}

function renderPages() {
  if (!cur) return;
  const n = step();
  if (n === 2) idx = idx - (idx % 2);
  const shown = cur.pages.slice(idx, idx + n);

  pagesEl.classList.toggle('two', shown.length === 2);
  pagesEl.replaceChildren(...shown.map(pg => {
    const img = new Image();
    img.src = pg.src; img.alt = `${cur.title} — ${pg.label}`;
    img.width = pg.w; img.height = pg.h; img.decoding = 'async';
    img.draggable = false;
    return img;
  }));

  stage.classList.toggle('fit-width', fitWidth);
  stage.scrollTop = 0;

  $('scrub').value = String(idx);
  $('counter').textContent = shown.length === 2
    ? `${idx + 1}–${idx + 2} / ${cur.pages.length}`
    : `${idx + 1} / ${cur.pages.length}`;
  $('prevBtn').disabled = idx <= 0;
  $('nextBtn').disabled = idx + n >= cur.pages.length;

  progress[cur.id] = idx; LS.set('progress', progress);
  preload(idx + n, 2 * n);
}

const preloaded = new Set();
function preload(from, count) {
  if (!cur) return;
  for (let i = from; i < Math.min(from + count, cur.pages.length); i++) {
    const src = cur.pages[i].src;
    if (preloaded.has(src)) continue;
    preloaded.add(src);
    const im = new Image(); im.decoding = 'async'; im.src = src;
  }
}

function go(delta) {
  if (!cur) return;
  const n = step();
  const next = idx + delta * n;
  if (next < 0 || next >= cur.pages.length) return;
  idx = next; renderPages(); showChrome();
}

/* 상·하단 바 자동 숨김 */
function showChrome(autohide = true) {
  readerEl.classList.remove('chrome-off');
  clearTimeout(chromeTimer);
  if (autohide) chromeTimer = setTimeout(() => readerEl.classList.add('chrome-off'), 2600);
}
function toggleChrome() {
  if (readerEl.classList.contains('chrome-off')) showChrome();
  else { clearTimeout(chromeTimer); readerEl.classList.add('chrome-off'); }
}

/* 화면 꺼짐 방지 */
async function requestWakeLock() {
  try { if ('wakeLock' in navigator) wakeLock = await navigator.wakeLock.request('screen'); } catch {}
}
function releaseWakeLock() { try { wakeLock?.release(); } catch {} wakeLock = null; }
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && cur) requestWakeLock(); else releaseWakeLock();
});

/* 조작 */
$('tapPrev').addEventListener('click', () => go(-1));
$('tapNext').addEventListener('click', () => go(1));
$('tapMid').addEventListener('click', toggleChrome);
$('prevBtn').addEventListener('click', () => go(-1));
$('nextBtn').addEventListener('click', () => go(1));
$('backBtn').addEventListener('click', () => { location.hash = '#/'; });
$('scrub').addEventListener('input', (e) => { idx = Number(e.target.value); renderPages(); showChrome(); });
$('favBtn').addEventListener('click', (e) => { toggleFav(cur.id); e.currentTarget.setAttribute('aria-pressed', String(favs.has(cur.id))); });
$('spreadBtn').addEventListener('click', (e) => {
  spread = !spread; LS.set('spread', spread);
  e.currentTarget.setAttribute('aria-pressed', String(spread));
  if (spread && !canSpread()) toast('가로 화면에서 두 장씩 보입니다');
  renderPages(); showChrome();
});
$('fitBtn').addEventListener('click', (e) => {
  fitWidth = !fitWidth; LS.set('fitWidth', fitWidth);
  e.currentTarget.setAttribute('aria-pressed', String(fitWidth));
  renderPages(); showChrome();
});
$('fsBtn').addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen({ navigationUI: 'hide' });
  } catch { toast('이 브라우저에서는 전체화면을 지원하지 않습니다'); }
  showChrome();
});

/* 스와이프 */
let sx = 0, sy = 0, st = 0, swiping = false;
stage.addEventListener('touchstart', (e) => {
  if (e.touches.length !== 1) { swiping = false; return; }
  swiping = true; sx = e.touches[0].clientX; sy = e.touches[0].clientY; st = Date.now();
}, { passive: true });
stage.addEventListener('touchend', (e) => {
  if (!swiping || !e.changedTouches.length) return;
  swiping = false;
  const dx = e.changedTouches[0].clientX - sx;
  const dy = e.changedTouches[0].clientY - sy;
  if (Date.now() - st < 600 && Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.6) go(dx < 0 ? 1 : -1);
}, { passive: true });

/* 키보드 */
addEventListener('keydown', (e) => {
  if (e.target.matches('input,textarea')) {
    if (e.key === 'Escape') e.target.blur();
    return;
  }
  if (!cur) {
    if (e.key === '/' ) { e.preventDefault(); $('q').focus(); }
    return;
  }
  switch (e.key) {
    case 'ArrowRight': case 'ArrowDown': case 'PageDown': case ' ': e.preventDefault(); go(1); break;
    case 'ArrowLeft': case 'ArrowUp': case 'PageUp': e.preventDefault(); go(-1); break;
    case 'Home': e.preventDefault(); idx = 0; renderPages(); showChrome(); break;
    case 'End': e.preventDefault(); idx = cur.pages.length - 1; renderPages(); showChrome(); break;
    case 'Escape': if (!document.fullscreenElement) location.hash = '#/'; break;
    case 'f': case 'F': $('fsBtn').click(); break;
    case 's': case 'S': $('spreadBtn').click(); break;
    case 'w': case 'W': $('fitBtn').click(); break;
    default: break;
  }
});

addEventListener('resize', () => { if (cur) renderPages(); });

/* ══════════════ 라우팅 ══════════════ */
function route() {
  const m = /^#\/p\/([^/]+)(?:\/(\d+))?/.exec(location.hash);
  if (m) openPiece(decodeURIComponent(m[1]), m[2] ? Number(m[2]) - 1 : undefined);
  else if (cur) closePiece();
}
addEventListener('hashchange', route);

/* ══════════════ 오프라인 저장 ══════════════ */
let swReg = null;
async function initSW() {
  if (!('serviceWorker' in navigator)) return;
  try {
    swReg = await navigator.serviceWorker.register('sw.js', { scope: './' });
    navigator.serviceWorker.addEventListener('message', (e) => {
      const d = e.data || {};
      if (d.type === 'prefetch-progress') {
        toast(`오프라인 저장 중… ${d.done}/${d.total}`, 0);
      } else if (d.type === 'prefetch-done') {
        toast(d.failed ? `저장 완료 (${d.failed}개 실패)` : '오프라인 저장 완료 — 이제 인터넷 없이 열립니다');
        updateOfflineStat();
      }
    });
  } catch {}
}
async function updateOfflineStat() {
  if (!('caches' in window)) return;
  try {
    const c = await caches.open('sl-scores-v1');
    const n = (await c.keys()).length;
    $('offstat').textContent = n ? `오프라인 저장됨 ${n}/${LIB.pageCount + LIB.pieces.length}` : '';
  } catch {}
}
$('offlineBtn').addEventListener('click', async () => {
  if (!navigator.serviceWorker?.controller) { toast('오프라인 기능을 준비 중입니다. 잠시 후 다시 눌러주세요'); return; }
  const urls = [];
  for (const p of LIB.pieces) { urls.push(p.cover.src); for (const pg of p.pages) urls.push(pg.src); }
  toast('오프라인 저장 시작…', 0);
  navigator.serviceWorker.controller.postMessage({ type: 'prefetch', urls });
});

/* ══════════════ 시작 ══════════════ */
(async function start() {
  try {
    const res = await fetch('library.json', { cache: 'no-cache' });
    LIB = await res.json();
  } catch {
    $('empty').hidden = false;
    $('empty').textContent = '악보 목록을 불러오지 못했습니다.';
    return;
  }
  byId = new Map(LIB.pieces.map(p => [p.id, p]));
  recent = recent.filter(id => byId.has(id));
  renderFilters(); renderGrid(); route();
  initSW().then(updateOfflineStat);
})();

})();
