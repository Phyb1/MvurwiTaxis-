// Served from the site root by taxis.views.service_worker (NOT from /static/)
// so its scope covers every page — required for Web Push on /dashboard/.
const CACHE_NAME = "mvurwitaxis-v2";
const OFFLINE_URL = "/";
const PRECACHE_URLS = [OFFLINE_URL, "/static/css/style.css"];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
    );
    self.skipWaiting();
});

self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

// Pages are network-first: the directory shows who is online right now, so a
// cached copy must only ever be an offline fallback, never the normal answer.
// Everything else (POSTs, images, static files) goes straight to the network.
self.addEventListener("fetch", (event) => {
    if (event.request.mode !== "navigate") return;
    event.respondWith(
        fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
});

// Web Push: display a notification when the server sends one (see
// taxis/utils/push.py). Payload is JSON: {title, body, url}.
self.addEventListener("push", (event) => {
    let payload = { title: "MvurwiTaxis", body: "You have a new notification.", url: "/" };
    try {
        if (event.data) payload = Object.assign(payload, event.data.json());
    } catch (e) {
        // Non-JSON payload — fall back to the defaults above.
    }
    event.waitUntil(
        self.registration.showNotification(payload.title, {
            body: payload.body,
            icon: "/static/img/icon-192.png",
            badge: "/static/img/icon-192.png",
            data: { url: payload.url },
        })
    );
});

self.addEventListener("notificationclick", (event) => {
    event.notification.close();
    const url = (event.notification.data && event.notification.data.url) || "/";
    event.waitUntil(clients.openWindow(url));
});
