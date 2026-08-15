/* シールノート Service Worker（要件14章）
   - 静的ファイルのキャッシュのみ。オフライン対応・バックグラウンド同期はしない
   - HTMLはキャッシュしない（古い記録が表示される事故を防ぐ）
   - CSS等を変更したら VERSION を上げる。activate で旧キャッシュを削除する */

const VERSION = "v4";
const CACHE_NAME = "sealnote-" + VERSION;

// 事前キャッシュする静的アセット（HTMLは含めない）
const PRECACHE = [
  "/static/css/style.css",
  "/static/js/app.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      // 一部が404でも全体が失敗しないよう個別に追加する
      Promise.all(
        PRECACHE.map((url) =>
          cache.add(url).catch(() => {
            /* 未配置のアイコン等は無視 */
          })
        )
      )
    )
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith("sealnote-") && key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;

  // GET以外は素通し
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // 静的ファイル以外（＝HTML等）はキャッシュしない。ネットワークに任せる。
  if (!url.pathname.startsWith("/static/")) return;

  // 静的ファイルは cache-first
  event.respondWith(
    caches.match(req).then((cached) => {
      if (cached) return cached;
      return fetch(req).then((res) => {
        // 正常なレスポンスのみ保存
        if (res && res.status === 200 && res.type === "basic") {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
        }
        return res;
      });
    })
  );
});
