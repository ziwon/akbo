/* score-leaf service worker
   - 앱 셸: stale-while-revalidate (새 배포가 다음 방문에 반영)
   - 악보 이미지: cache-first (내용이 바뀌지 않음)
   - postMessage {type:'prefetch', urls} 로 전체 오프라인 저장 */

const SHELL = 'sl-shell-v1';
const SCORES = 'sl-scores-v1';
const SHELL_FILES = [
  './', './index.html', './styles.css', './app.js',
  './library.json', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    await Promise.allSettled(SHELL_FILES.map((f) => c.add(new Request(f, { cache: 'reload' }))));
    self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keep = new Set([SHELL, SCORES]);
    for (const k of await caches.keys()) if (!keep.has(k)) await caches.delete(k);
    await self.clients.claim();
  })());
});

const isScore = (url) => url.pathname.includes('/scores/');

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (isScore(url)) {
    e.respondWith((async () => {
      const c = await caches.open(SCORES);
      const hit = await c.match(req);
      if (hit) return hit;
      try {
        const res = await fetch(req);
        if (res.ok) c.put(req, res.clone());
        return res;
      } catch (err) {
        return hit || Response.error();
      }
    })());
    return;
  }

  // 앱 셸 + library.json
  e.respondWith((async () => {
    const c = await caches.open(SHELL);
    const hit = await c.match(req, { ignoreSearch: true });
    const net = fetch(req).then((res) => {
      if (res.ok) c.put(req, res.clone());
      return res;
    }).catch(() => null);
    if (hit) { net; return hit; }
    const res = await net;
    if (res) return res;
    if (req.mode === 'navigate') {
      const shell = await c.match('./index.html');
      if (shell) return shell;
    }
    return Response.error();
  })());
});

self.addEventListener('message', (e) => {
  const d = e.data || {};
  if (d.type !== 'prefetch' || !Array.isArray(d.urls)) return;

  e.waitUntil((async () => {
    const c = await caches.open(SCORES);
    const client = e.source;
    const total = d.urls.length;
    let done = 0, failed = 0, lastPost = 0;
    const CONCURRENCY = 6;
    const queue = d.urls.slice();

    async function worker() {
      while (queue.length) {
        const u = queue.shift();
        try {
          if (!(await c.match(u))) {
            const res = await fetch(u, { cache: 'no-cache' });
            if (res.ok) await c.put(u, res.clone()); else failed++;
          }
        } catch { failed++; }
        done++;
        const now = Date.now();
        if (client && (now - lastPost > 250 || done === total)) {
          lastPost = now;
          client.postMessage({ type: 'prefetch-progress', done, total });
        }
      }
    }
    await Promise.all(Array.from({ length: CONCURRENCY }, worker));
    client?.postMessage({ type: 'prefetch-done', total, failed });
  })());
});
