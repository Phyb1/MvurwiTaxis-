// Registers the PWA service worker. Kept minimal per PHYB convention of
// hand-written, dependency-free JS.
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/service-worker.js", { scope: "/" }).catch(() => {
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
        const response = await fetch("/push/subscribe/", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify(subscription.toJSON()),
        });
        if (!response.ok) throw new Error("Server rejected the subscription");
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

// "Bookmark this site" banner (templates/base.html#bookmark-prompt).
// There's no browser API to open the native bookmark dialog (unlike
// beforeinstallprompt for PWA install above), so this is a nudge with
// platform-specific instructions, not a one-tap action.
(function initBookmarkPrompt() {
    const DISMISS_KEY = "mvurwitaxis:bookmark-prompt-dismissed-until";
    const DISMISS_DAYS_NOT_NOW = 30;   // ask again in a month
    const DISMISS_DAYS_ACCEPTED = 365; // they said "Got it" — stop asking
    const SHOW_AFTER_MS = 12000;
    // Driver-only pages: drivers already return via login, don't nag them.
    const SKIP_PATH_PREFIXES = ["/dashboard/", "/login/", "/signup/", "/admin"];

    function isStandalone() {
        return (
            window.matchMedia("(display-mode: standalone)").matches ||
            window.navigator.standalone === true // iOS Safari home-screen launch
        );
    }

    function isDismissed() {
        const until = Number(localStorage.getItem(DISMISS_KEY) || 0);
        return Date.now() < until;
    }

    function dismiss(days) {
        const until = Date.now() + days * 24 * 60 * 60 * 1000;
        try {
            localStorage.setItem(DISMISS_KEY, String(until));
        } catch (e) {
            // Private browsing may block localStorage writes — banner will
            // just reappear next visit, which is an acceptable fallback.
        }
    }

    function hintText() {
        const ua = navigator.userAgent;
        const isMac = /Macintosh/.test(ua) && !/iPhone|iPad/.test(ua);
        const isIOS = /iPhone|iPad|iPod/.test(ua);
        const isAndroid = /Android/.test(ua);
        if (isIOS) return "Tap Share, then \"Add to Home Screen\".";
        if (isAndroid) return "Tap the menu (\u22ee), then \"Add to Home screen\".";
        if (isMac) return "Press Cmd+D to bookmark this page.";
        return "Press Ctrl+D to bookmark this page.";
    }

    document.addEventListener("DOMContentLoaded", () => {
        const banner = document.getElementById("bookmark-prompt");
        if (!banner) return;

        const path = window.location.pathname;
        if (SKIP_PATH_PREFIXES.some((prefix) => path.startsWith(prefix))) return;
        if (isStandalone() || isDismissed()) return;

        window.setTimeout(() => {
            const hint = document.getElementById("bookmark-prompt-hint");
            if (hint) hint.textContent = hintText();
            banner.hidden = false;
        }, SHOW_AFTER_MS);

        const dismissBtn = document.getElementById("bookmark-prompt-dismiss");
        if (dismissBtn) {
            dismissBtn.addEventListener("click", () => {
                banner.hidden = true;
                dismiss(DISMISS_DAYS_NOT_NOW);
            });
        }

        // "Got it": on Chrome/Android with an install prompt already
        // captured (see beforeinstallprompt above), actually trigger it —
        // that's the closest thing to a one-tap "save this" action that
        // exists. Everywhere else there's no browser API for it, so this
        // just acknowledges the on-screen instructions and stops asking.
        const acceptBtn = document.getElementById("bookmark-prompt-accept");
        if (acceptBtn) {
            acceptBtn.addEventListener("click", () => {
                if (deferredInstallPrompt) installApp();
                banner.hidden = true;
                dismiss(DISMISS_DAYS_ACCEPTED);
            });
        }
    });
})();
