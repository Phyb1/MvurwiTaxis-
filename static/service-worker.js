const CACHE_NAME = "mvurwitaxis-v1";
const OFFLINE_URLS = ["/", "/static/css/style.css"];

self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(OFFLINE_URLS))
    );
});

self.addEventListener("fetch", (event) => {
    event.respondWith(
        caches.match(event.request).then((cached) => cached || fetch(event.request))
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
