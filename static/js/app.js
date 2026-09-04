// Registers the PWA service worker. Kept minimal per PHYB convention of
// hand-written, dependency-free JS.
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/static/service-worker.js").catch(() => {
            // Silent fail: PWA install is a nice-to-have, not a blocker.
        });
    });
}

function copyShareText(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert("Copied! Paste it into your WhatsApp Status or a group.");
    });
}
