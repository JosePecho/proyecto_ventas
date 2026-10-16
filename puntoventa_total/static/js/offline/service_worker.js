/* Service worker: cache de assets y fallback offline */
const CACHE = "puntoventa-v1";
const ASSETS = [
  "/static/css/base.css",
  "/static/css/pos.css",
  "/static/js/main.js",
  "/static/js/offline/indexed_db.js",
  "/static/js/offline/offline_queue.js",
  "/static/js/offline/sync_manager.js",
  "/static/js/offline/conflict_resolver.js",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((claves) => Promise.all(claves.filter((c) => c !== CACHE).map((c) => caches.delete(c))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  if (evento.request.method !== "GET") return;
  evento.respondWith(
    fetch(evento.request)
      .then((respuesta) => {
        const copia = respuesta.clone();
        caches.open(CACHE).then((cache) => cache.put(evento.request, copia));
        return respuesta;
      })
      .catch(() => caches.match(evento.request))
  );
});

