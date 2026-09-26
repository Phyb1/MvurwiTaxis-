// ============================================================
// MvurwiTaxis - Main JavaScript
// ============================================================


// ============================================================
// SERVICE WORKER / PWA
// ============================================================

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker
            .register("/service-worker.js", { scope: "/" })
            .then((registration) => {
                console.log("Service worker registered:", registration.scope);
            })
            .catch((error) => {
                console.error("Service worker registration failed:", error);
            });
    });
}


// ============================================================
// ADD TO HOME SCREEN
// ============================================================

let deferredInstallPrompt = null;

window.addEventListener("beforeinstallprompt", (event) => {
    event.preventDefault();

    deferredInstallPrompt = event;

    const btn = document.getElementById("install-app-btn");

    if (btn) {
        btn.hidden = false;
    }
});

function installApp() {
    if (!deferredInstallPrompt) {
        return;
    }

    deferredInstallPrompt.prompt();

    deferredInstallPrompt.userChoice
        .then(() => {
            deferredInstallPrompt = null;

            const btn = document.getElementById("install-app-btn");

            if (btn) {
                btn.hidden = true;
            }
        })
        .catch((error) => {
            console.error("Install prompt error:", error);
            deferredInstallPrompt = null;
        });
}


// ============================================================
// WEB PUSH NOTIFICATIONS
// ============================================================

function urlBase64ToUint8Array(base64String) {
    const padding = "=".repeat(
        (4 - (base64String.length % 4)) % 4
    );

    const base64 = (
        base64String + padding
    )
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    const rawData = window.atob(base64);

    return Uint8Array.from(
        [...rawData].map((character) => character.charCodeAt(0))
    );
}


async function enablePushNotifications(button) {

    // --------------------------------------------------------
    // Browser support checks
    // --------------------------------------------------------

    if (!("serviceWorker" in navigator)) {
        alert(
            "Your browser does not support service workers, " +
            "so push notifications cannot be enabled."
        );
        return;
    }

    if (!("PushManager" in window)) {
        alert(
            "Your browser does not support push notifications."
        );
        return;
    }

    if (!("Notification" in window)) {
        alert(
            "Your browser does not support browser notifications."
        );
        return;
    }


    // --------------------------------------------------------
    // Read values supplied by Django
    // --------------------------------------------------------

    const vapidPublicKey = button.dataset.vapidKey;
    const csrfToken = button.dataset.csrf;


    if (!vapidPublicKey) {
        console.error("Missing VAPID public key.");
        alert(
            "Push notifications are not configured correctly " +
            "on the server. The VAPID public key is missing."
        );
        return;
    }

    if (!csrfToken) {
        console.error("Missing CSRF token.");
        alert(
            "Security token missing. Please refresh the page " +
            "and try again."
        );
        return;
    }


    try {

        // ----------------------------------------------------
        // Ask the browser for notification permission
        // ----------------------------------------------------

        let permission = Notification.permission;

        console.log(
            "Current notification permission:",
            permission
        );


        if (permission === "default") {

            permission = await Notification.requestPermission();

            console.log(
                "Notification permission after request:",
                permission
            );
        }


        if (permission !== "granted") {

            if (permission === "denied") {
                alert(
                    "Notifications are blocked for MvurwiTaxis.\n\n" +
                    "Open your browser's site settings for " +
                    "mvurwitaxis.co.zw and allow notifications, " +
                    "then return here and try again."
                );
            } else {
                alert(
                    "Notification permission was not granted."
                );
            }

            return;
        }


        // ----------------------------------------------------
        // Wait for service worker
        // ----------------------------------------------------

        console.log("Waiting for service worker...");

        const registration =
            await navigator.serviceWorker.ready;

        console.log(
            "Service worker ready:",
            registration
        );


        // ----------------------------------------------------
        // Check for an existing subscription
        // ----------------------------------------------------

        let subscription =
            await registration.pushManager.getSubscription();


        // ----------------------------------------------------
        // Create a new subscription if necessary
        // ----------------------------------------------------

        if (!subscription) {

            console.log(
                "No existing push subscription. Creating one..."
            );

            subscription =
                await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey:
                        urlBase64ToUint8Array(vapidPublicKey),
                });

        } else {

            console.log(
                "Existing push subscription found."
            );
        }


        console.log(
            "Push subscription:",
            subscription
        );


        // ----------------------------------------------------
        // Send subscription to Django
        // ----------------------------------------------------

        const response = await fetch(
            "/push/subscribe/",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },

                body: JSON.stringify(
                    subscription.toJSON()
                ),
            }
        );


        // ----------------------------------------------------
        // Handle server response
        // ----------------------------------------------------

        if (!response.ok) {

            let serverMessage = "";

            try {
                serverMessage = await response.text();
            } catch (error) {
                console.error(
                    "Could not read server response:",
                    error
                );
            }

            console.error(
                "Push subscription request failed:",
                response.status,
                serverMessage
            );

            throw new Error(
                `Server rejected the subscription ` +
                `(${response.status}). ${serverMessage}`
            );
        }


        console.log(
            "Push subscription successfully saved."
        );


        // ----------------------------------------------------
        // Update button
        // ----------------------------------------------------

        button.textContent = "Notifications enabled";
        button.disabled = true;


        // ----------------------------------------------------
        // Success message
        // ----------------------------------------------------

        alert(
            "Notifications enabled successfully."
        );

    } catch (error) {

        // ----------------------------------------------------
        // IMPORTANT:
        // Show the REAL error instead of hiding it.
        // ----------------------------------------------------

        console.error(
            "Push notification error:",
            error
        );


        let message =
            error && error.message
                ? error.message
                : String(error);


        alert(
            "Couldn't enable notifications.\n\n" +
            "Error: " +
            message
        );
    }
}


// ============================================================
// COPY SHARE TEXT
// ============================================================

function copyShareText(text) {

    navigator.clipboard
        .writeText(text)
        .then(() => {
            alert(
                "Copied! Paste it into your WhatsApp Status or a group."
            );
        })
        .catch((error) => {

            console.error(
                "Clipboard error:",
                error
            );

            alert(
                "Couldn't copy the text."
            );
        });
}


// ============================================================
// BOOKMARK PROMPT
// ============================================================

(function initBookmarkPrompt() {

    const DISMISS_KEY =
        "mvurwitaxis:bookmark-prompt-dismissed-until";

    const DISMISS_DAYS_NOT_NOW = 30;

    const DISMISS_DAYS_ACCEPTED = 365;

    const SHOW_AFTER_MS = 12000;


    // Driver-only pages:
    // drivers already return via login, don't nag them.
    const SKIP_PATH_PREFIXES = [
        "/dashboard/",
        "/login/",
        "/signup/",
        "/admin",
    ];


    function isStandalone() {

        return (
            window.matchMedia(
                "(display-mode: standalone)"
            ).matches ||

            window.navigator.standalone === true
        );
    }


    function isDismissed() {

        const until = Number(
            localStorage.getItem(DISMISS_KEY) || 0
        );

        return Date.now() < until;
    }


    function dismiss(days) {

        const until =
            Date.now() +
            days * 24 * 60 * 60 * 1000;

        try {

            localStorage.setItem(
                DISMISS_KEY,
                String(until)
            );

        } catch (error) {

            console.warn(
                "Could not save bookmark prompt state:",
                error
            );
        }
    }


    function hintText() {

        const ua = navigator.userAgent;

        const isMac =
            /Macintosh/.test(ua) &&
            !/iPhone|iPad/.test(ua);

        const isIOS =
            /iPhone|iPad|iPod/.test(ua);

        const isAndroid =
            /Android/.test(ua);


        if (isIOS) {
            return "Tap Share, then \"Add to Home Screen\".";
        }

        if (isAndroid) {
            return "Tap the menu (\u22ee), then \"Add to Home screen\".";
        }

        if (isMac) {
            return "Press Cmd+D to bookmark this page.";
        }

        return "Press Ctrl+D to bookmark this page.";
    }


    document.addEventListener(
        "DOMContentLoaded",
        () => {

            const banner =
                document.getElementById(
                    "bookmark-prompt"
                );

            if (!banner) {
                return;
            }


            const path =
                window.location.pathname;


            if (
                SKIP_PATH_PREFIXES.some(
                    (prefix) =>
                        path.startsWith(prefix)
                )
            ) {
                return;
            }


            if (
                isStandalone() ||
                isDismissed()
            ) {
                return;
            }


            window.setTimeout(() => {

                const hint =
                    document.getElementById(
                        "bookmark-prompt-hint"
                    );

                if (hint) {
                    hint.textContent =
                        hintText();
                }

                banner.hidden = false;

            }, SHOW_AFTER_MS);


            const dismissBtn =
                document.getElementById(
                    "bookmark-prompt-dismiss"
                );


            if (dismissBtn) {

                dismissBtn.addEventListener(
                    "click",
                    () => {

                        banner.hidden = true;

                        dismiss(
                            DISMISS_DAYS_NOT_NOW
                        );
                    }
                );
            }


            const acceptBtn =
                document.getElementById(
                    "bookmark-prompt-accept"
                );


            if (acceptBtn) {

                acceptBtn.addEventListener(
                    "click",
                    () => {

                        if (deferredInstallPrompt) {
                            installApp();
                        }

                        banner.hidden = true;

                        dismiss(
                            DISMISS_DAYS_ACCEPTED
                        );
                    }
                );
            }
        }
    );

})();
