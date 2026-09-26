// ============================================================
// MvurwiTaxis - Main JavaScript
// PWA + Web Push Notifications + Sharing + Bookmark Prompt
// ============================================================


// ============================================================
// SERVICE WORKER / PWA
// ============================================================

if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker
            .register("/service-worker.js", { scope: "/" })
            .then((registration) => {
                console.log(
                    "MvurwiTaxis service worker registered:",
                    registration.scope
                );
            })
            .catch((error) => {
                console.error(
                    "MvurwiTaxis service worker registration failed:",
                    error
                );
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
        console.log("No install prompt is currently available.");
        return;
    }

    deferredInstallPrompt.prompt();

    deferredInstallPrompt.userChoice.finally(() => {
        deferredInstallPrompt = null;

        const btn = document.getElementById("install-app-btn");

        if (btn) {
            btn.hidden = true;
        }
    });
}


// ============================================================
// WEB PUSH HELPERS
// ============================================================

function urlBase64ToUint8Array(base64String) {
    if (!base64String) {
        throw new Error("VAPID public key is empty.");
    }

    const padding =
        "=".repeat((4 - (base64String.length % 4)) % 4);

    const base64 = (base64String + padding)
        .replace(/-/g, "+")
        .replace(/_/g, "/");

    let rawData;

    try {
        rawData = window.atob(base64);
    } catch (error) {
        throw new Error("The VAPID public key is not valid Base64.");
    }

    return Uint8Array.from(
        [...rawData].map((character) => character.charCodeAt(0))
    );
}


// ============================================================
// ENABLE PUSH NOTIFICATIONS
// ============================================================

async function enablePushNotifications(button) {

    const originalText = button.textContent;

    try {

        console.log("====================================");
        console.log("Starting push notification setup...");
        console.log("====================================");


        // --------------------------------------------------------
        // 1. Browser support
        // --------------------------------------------------------

        button.disabled = true;
        button.textContent = "Checking notifications...";

        if (!("serviceWorker" in navigator)) {
            throw new Error(
                "This browser does not support service workers."
            );
        }

        if (!("PushManager" in window)) {
            throw new Error(
                "This browser does not support Web Push notifications."
            );
        }

        if (!("Notification" in window)) {
            throw new Error(
                "This browser does not support browser notifications."
            );
        }


        // --------------------------------------------------------
        // 2. Read values from the button
        // --------------------------------------------------------

        const vapidPublicKey = button.dataset.vapidKey;
        const csrfToken = button.dataset.csrf;

        console.log(
            "VAPID public key present:",
            Boolean(vapidPublicKey)
        );

        console.log(
            "CSRF token present:",
            Boolean(csrfToken)
        );

        if (!vapidPublicKey) {
            throw new Error(
                "VAPID public key is missing from the page."
            );
        }

        if (!csrfToken) {
            throw new Error(
                "CSRF token is missing from the notification button."
            );
        }


        // --------------------------------------------------------
        // 3. Ask for notification permission
        // --------------------------------------------------------

        button.textContent = "Checking permission...";

        let permission = Notification.permission;

        console.log(
            "Current notification permission:",
            permission
        );

        if (permission === "default") {

            button.textContent = "Allow notifications...";

            permission = await Notification.requestPermission();

            console.log(
                "Notification permission result:",
                permission
            );
        }

        if (permission !== "granted") {

            throw new Error(
                "Notification permission is '" +
                permission +
                "'. Please allow notifications for mvurwitaxis.co.zw."
            );
        }


        // --------------------------------------------------------
        // 4. Register service worker
        // --------------------------------------------------------

        button.textContent = "Registering notifications...";

        console.log(
            "Registering /service-worker.js..."
        );

        const registration =
            await navigator.serviceWorker.register(
                "/service-worker.js",
                {
                    scope: "/"
                }
            );

        console.log(
            "Service worker registration successful:",
            registration
        );


        // --------------------------------------------------------
        // 5. Wait for service worker to become active
        // --------------------------------------------------------

        button.textContent = "Starting notification service...";

        if (!registration.active) {

            console.log(
                "Service worker is not active yet."
            );

            await new Promise((resolve, reject) => {

                const timeout = setTimeout(() => {

                    reject(
                        new Error(
                            "Service worker did not become active within 15 seconds."
                        )
                    );

                }, 15000);


                // Service worker is installing
                if (registration.installing) {

                    const worker = registration.installing;

                    console.log(
                        "Service worker state:",
                        worker.state
                    );

                    const checkState = () => {

                        console.log(
                            "Service worker state:",
                            worker.state
                        );

                        if (worker.state === "activated") {

                            clearTimeout(timeout);
                            resolve();

                        } else if (worker.state === "redundant") {

                            clearTimeout(timeout);

                            reject(
                                new Error(
                                    "Service worker became redundant."
                                )
                            );
                        }
                    };

                    worker.addEventListener(
                        "statechange",
                        checkState
                    );

                    // It may have changed before listener attached.
                    checkState();

                }

                // Service worker waiting
                else if (registration.waiting) {

                    const worker = registration.waiting;

                    console.log(
                        "Service worker is waiting."
                    );

                    const checkState = () => {

                        console.log(
                            "Waiting service worker state:",
                            worker.state
                        );

                        if (worker.state === "activated") {

                            clearTimeout(timeout);
                            resolve();

                        } else if (worker.state === "redundant") {

                            clearTimeout(timeout);

                            reject(
                                new Error(
                                    "Waiting service worker became redundant."
                                )
                            );
                        }
                    };

                    worker.addEventListener(
                        "statechange",
                        checkState
                    );

                    checkState();

                }

                else {

                    clearTimeout(timeout);

                    reject(
                        new Error(
                            "Service worker could not be installed."
                        )
                    );
                }

            });
        }


        // --------------------------------------------------------
        // 6. Get existing subscription
        // --------------------------------------------------------

        button.textContent = "Checking subscription...";

        console.log(
            "Getting existing push subscription..."
        );

        let subscription =
            await registration.pushManager.getSubscription();


        // --------------------------------------------------------
        // 7. Create subscription if necessary
        // --------------------------------------------------------

        if (!subscription) {

            button.textContent =
                "Creating notification subscription...";

            console.log(
                "No existing subscription found."
            );

            console.log(
                "Creating new push subscription..."
            );

            const applicationServerKey =
                urlBase64ToUint8Array(vapidPublicKey);

            console.log(
                "VAPID key converted successfully."
            );

            subscription =
                await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey:
                        applicationServerKey
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


        // --------------------------------------------------------
        // 8. Send subscription to Django
        // --------------------------------------------------------

        button.textContent =
            "Saving notification settings...";

        console.log(
            "Sending subscription to Django..."
        );

        const response = await fetch(
            "/push/subscribe/",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken
                },

                credentials: "same-origin",

                body: JSON.stringify(
                    subscription.toJSON()
                )
            }
        );


        const responseText =
            await response.text();


        console.log(
            "Django response:",
            response.status,
            responseText
        );


        if (!response.ok) {

            throw new Error(
                "Server rejected the subscription (" +
                response.status +
                "): " +
                responseText
            );
        }


        // --------------------------------------------------------
        // 9. Success
        // --------------------------------------------------------

        button.textContent =
            "Notifications enabled";

        button.disabled = true;

        console.log(
            "===================================="
        );

        console.log(
            "Push notifications enabled successfully."
        );

        console.log(
            "===================================="
        );

        alert(
            "Notifications enabled successfully."
        );

    } catch (error) {

        console.error(
            "===================================="
        );

        console.error(
            "PUSH NOTIFICATION ERROR:",
            error
        );

        console.error(
            "===================================="
        );


        // Restore button
        button.disabled = false;

        button.textContent = originalText;


        alert(
            "Push notification setup failed:\n\n" +
            error.message
        );
    }
}


// ============================================================
// COPY SHARE TEXT
// ============================================================

function copyShareText(text) {

    if (!navigator.clipboard) {

        alert(
            "Copy is not supported by this browser."
        );

        return;
    }

    navigator.clipboard
        .writeText(text)
        .then(() => {

            alert(
                "Copied! Paste it into your WhatsApp Status or a group."
            );

        })
        .catch((error) => {

            console.error(
                "Copy failed:",
                error
            );

            alert(
                "Couldn't copy the text. Please copy it manually."
            );
        });
}


// ============================================================
// BOOKMARK / INSTALL PROMPT
// ============================================================

(function initBookmarkPrompt() {

    const DISMISS_KEY =
        "mvurwitaxis:bookmark-prompt-dismissed-until";

    const DISMISS_DAYS_NOT_NOW = 30;

    const DISMISS_DAYS_ACCEPTED = 365;

    const SHOW_AFTER_MS = 12000;


    // Driver-only pages should not show the prompt.
    const SKIP_PATH_PREFIXES = [
        "/dashboard/",
        "/login/",
        "/signup/",
        "/admin"
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

        const until =
            Number(
                localStorage.getItem(
                    DISMISS_KEY
                ) || 0
            );

        return Date.now() < until;
    }


    function dismiss(days) {

        const until =
            Date.now() +
            days *
            24 *
            60 *
            60 *
            1000;

        try {

            localStorage.setItem(
                DISMISS_KEY,
                String(until)
            );

        } catch (error) {

            console.warn(
                "Could not save bookmark prompt preference:",
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

            return "Tap the menu (⋮), then \"Add to Home screen\".";

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


            window.setTimeout(
                () => {

                    const hint =
                        document.getElementById(
                            "bookmark-prompt-hint"
                        );


                    if (hint) {

                        hint.textContent =
                            hintText();

                    }


                    banner.hidden = false;

                },
                SHOW_AFTER_MS
            );


            // ----------------------------------------------------
            // Not now
            // ----------------------------------------------------

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


            // ----------------------------------------------------
            // Got it / Install
            // ----------------------------------------------------

            const acceptBtn =
                document.getElementById(
                    "bookmark-prompt-accept"
                );


            if (acceptBtn) {

                acceptBtn.addEventListener(
                    "click",
                    () => {

                        if (
                            deferredInstallPrompt
                        ) {

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
