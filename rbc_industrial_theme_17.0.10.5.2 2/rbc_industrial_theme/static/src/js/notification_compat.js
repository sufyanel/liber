/** @odoo-module */
// Compatibility layer: some installed add-ons still pass Odoo 16 notification
// buttons ({text, click, close}). Odoo 17's Notification component only accepts
// {name, onClick, primary} and throws "Invalid props for component 'Notification'"
// (seen when clicking Add to cart). Convert the old shape before it renders.
import { registry } from "@web/core/registry";

const services = registry.category("services");
const original = services.get("notification", null);
if (original && !original.__legacyButtonsCompat) {
    services.add("notification", {
        ...original,
        __legacyButtonsCompat: true,
        start(env, deps) {
            const api = original.start(env, deps);
            const add = api.add;
            return Object.assign({}, api, {
                add(message, options = {}) {
                    // session_expired_redirect: the installed Liber theme makes cart routes login-only;
                    // instead of the "Odoo Session Expired" popup, send the visitor to log in and come back.
                    const txt = String((options && options.title) || "") + " " + String(message || "");
                    const html = document.documentElement;
                    if (/session expired/i.test(txt) && (html.getAttribute("data-rbc-theme") === "1" || html.getAttribute("data-tc-theme") === "1")) {
                        window.location.href = "/web/login?redirect=" + encodeURIComponent(window.location.pathname + window.location.search);
                        return () => {};
                    }
                    if (options && Array.isArray(options.buttons)) {
                        options = Object.assign({}, options, {
                            buttons: options.buttons.map((b) => {
                                if (b && typeof b.onClick === "function" && typeof b.name === "string") {
                                    return b;
                                }
                                const legacyClick = b && (b.click || b.onClick);
                                return {
                                    name: String((b && (b.name || b.text)) || ""),
                                    primary: Boolean(b && (b.primary || String(b.classes || "").includes("primary"))),
                                    onClick: () => { if (typeof legacyClick === "function") { legacyClick(); } },
                                };
                            }),
                        });
                    }
                    return add.call(api, message, options);
                },
            });
        },
    }, { force: true });
}
