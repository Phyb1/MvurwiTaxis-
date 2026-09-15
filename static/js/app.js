// Registers the PWA service worker. Kept minimal per PHYB convention of
// hand-written, dependency-free JS.
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/static/service-worker.js").catch(() => {
            // Silent fail: PWA install is a nice-to-have, not a blocker.
        });
    });
}

// "Add to Home Screen" prompt. Chrome/Android fires beforeinstallprompt;
// iOS Safari never does (no programmatic install API there — the
// apple-mobile-web-app meta tags in base.html + manual "Share > Add to
// Home Screen" is the only path on iOS, nothing to wire up in JS for it).
let deferredInstallPrompt = null;
window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();
    deferredInstallPrompt = event;
    const btn = document.getElementById("install-app-btn");
    if (btn) btn.hidden = false;
});

function installApp() {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    deferredInstallPrompt.userChoice.finally(() => {
        deferredInstallPrompt = null;
        const btn = document.getElementById("install-app-btn");
        if (btn) btn.hidden = true;
    });
}

// Web Push subscribe/unsubscribe. Called from the dashboard's
// "Enable notifications" button (see dashboard.html). vapidPublicKey and
// the CSRF token are read from data-* attributes on that button so this
// file stays free of server-rendered values.
function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const rawData = window.atob(base64);
    return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

async function enablePushNotifications(button) {
    if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
        alert("Push notifications aren't supported in this browser.");
        return;
    }
    const vapidPublicKey = button.dataset.vapidKey;
    const csrfToken = button.dataset.csrf;
    try {
        const registration = await navigator.serviceWorker.ready;
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
        });
        await fetch("/push/subscribe/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify(subscription.toJSON()),
        });
        button.textContent = "Notifications enabled";
        button.disabled = true;
    } catch (err) {
        alert("Couldn't enable notifications — you may need to allow them in your browser settings.");
    }
}

function copyShareText(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert("Copied! Paste it into your WhatsApp Status or a group.");
    });
}
