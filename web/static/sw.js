// Claudio Radio service worker — minimal shell.
// Music streams and API responses are intentionally NOT cached:
// Netease URLs are short-lived and AI replies are context-dependent.

const CACHE = "claudio-shell-v10";
const SHELL = [
  "/",
  "/static/schedule.css",
  "/static/schedule.js",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
  "/static/icons/apple-touch-icon.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(SHELL)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  // Never cache API or audio — always hit network.
  if (url.pathname.startsWith("/api/") || url.pathname.startsWith("/audio/")) {
    return;
  }
  // Cache-first for static shell; fall back to network.
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
