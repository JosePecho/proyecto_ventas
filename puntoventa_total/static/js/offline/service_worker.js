/* Service worker: cache de assets y fallback offline */
const CACHE = "puntoventa-assets-v2";
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
    caches.keys().then((claves) => Promise.all(claves.filter((c) => c.startsWith("puntoventa-") && c !== CACHE).map((c) => caches.delete(c))))
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  const url = new URL(evento.request.url);
  // Nunca guardar paginas privadas, tickets ni respuestas de otros dominios.
  if (evento.request.method !== "GET" || url.origin !== self.location.origin || !url.pathname.startsWith("/static/")) return;
  evento.respondWith(
    fetch(evento.request)
      .then((respuesta) => {
        const copia = respuesta.clone();
        if (respuesta.ok) evento.waitUntil(caches.open(CACHE).then((cache) => cache.put(evento.request, copia)));
        return respuesta;
      })
      .catch(() => caches.match(evento.request))
  );
});

