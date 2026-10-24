/* Globe Electric Supply
   1. UTM passthrough: captures campaign parameters on the landing page, keeps them
      for the session, and fills the hidden fields on the quote form. Never shown.
   2. GA4 generate_lead on /quote-received, retried until gtag is ready, with no
      value field so GA4 applies the key-event default. */
(function () {
    "use strict";
    var root = document.documentElement;
    if (root.getAttribute("data-globe-theme") !== "1") { return; }

    var KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid"];
    var STORE = "globe_utm";

    function readStore() {
        try { return JSON.parse(window.sessionStorage.getItem(STORE) || "{}"); } catch (e) { return {}; }
    }
    function writeStore(data) {
        try { window.sessionStorage.setItem(STORE, JSON.stringify(data)); } catch (e) { /* private mode */ }
    }

    function captureUtm() {
        var data = readStore();
        var params = new URLSearchParams(window.location.search);
        var found = false;
        KEYS.forEach(function (key) {
            var v = params.get(key);
            if (v) { data[key] = v; found = true; }
        });
        if (!data.landing_page) { data.landing_page = window.location.pathname + window.location.search; }
        if (!data.referrer && document.referrer && document.referrer.indexOf(window.location.host) === -1) {
            data.referrer = document.referrer;
        }
        // lead_source: the campaign source if there is one, otherwise the referring site, otherwise direct
        if (!data.lead_source) {
            var host = "";
            try { host = data.referrer ? new URL(data.referrer).hostname : ""; } catch (e) { host = ""; }
            data.lead_source = data.utm_source || host || "direct";
        }
        if (found || !readStore().landing_page) { writeStore(data); }
        return data;
    }

    function fillForm(data) {
        document.querySelectorAll("input[data-globe-utm]").forEach(function (input) {
            var key = input.getAttribute("data-globe-utm");
            if (data[key]) { input.value = data[key]; }
        });
    }

    function fireLead() {
        var marker = document.querySelector("[data-globe-lead-event]");
        if (!marker || marker.getAttribute("data-fired") === "1") { return; }
        marker.setAttribute("data-fired", "1");
        var source = marker.getAttribute("data-globe-lead-source") || "globe_rfq";
        var tries = 0;
        (function send() {
            if (typeof window.gtag === "function") {
                window.gtag("event", "generate_lead", { lead_source: source, currency: "USD" });
                return;
            }
            tries += 1;
            if (tries < 20) { window.setTimeout(send, 250); return; }
            // No gtag after 5 seconds: hand the event to Tag Manager instead.
            window.dataLayer = window.dataLayer || [];
            window.dataLayer.push({ event: "generate_lead", lead_source: source, currency: "USD" });
        })();
    }

    function bindMenu() {
        document.querySelectorAll("[data-globe-toggle]").forEach(function (btn) {
            var target = document.getElementById(btn.getAttribute("data-globe-toggle"));
            if (!target) { return; }
            btn.addEventListener("click", function () {
                var open = target.classList.toggle("show");
                btn.setAttribute("aria-expanded", open ? "true" : "false");
            });
        });
    }

    function start() {
        fillForm(captureUtm());
        fireLead();
        bindMenu();
    }
    if (document.readyState !== "loading") { start(); } else { document.addEventListener("DOMContentLoaded", start); }
})();

/* Globe catalog: value search inside long filter groups; click a row or card to open the product */
(function () {
    "use strict";
    function norm(s) { return (s || "").toLowerCase().replace(/\s+/g, " ").trim(); }
    function ready(fn) { if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", fn); } else { fn(); } }
    ready(function () {
        if (document.documentElement.getAttribute("data-globe-theme") !== "1") { return; }
        var grid = document.getElementById("products_grid");
        if (!grid) { return; }
        var input = grid.querySelector(".products_header input[name='search']");
        if (input) { input.setAttribute("placeholder", "Search by part number, brand or spec\u2026"); }
        Array.prototype.forEach.call(document.querySelectorAll(".gcat-value-search"), function (box) {
            box.addEventListener("input", function () {
                var q = norm(box.value);
                Array.prototype.forEach.call(box.parentElement.querySelectorAll(".gcat-check"), function (l) {
                    l.classList.toggle("gcat-qf-hide", !(!q || norm(l.textContent).indexOf(q) !== -1));
                });
            });
            box.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); } });
        });
        grid.addEventListener("click", function (ev) {
            var row = ev.target.closest(".gcat-table tbody tr, .gcat-pcard");
            if (!row || ev.target.closest("a, button, input, label, form")) { return; }
            if (window.getSelection && String(window.getSelection()).length) { return; }
            var link = row.querySelector(".gcat-pname, .gcat-part");
            if (!link) { return; }
            if (ev.ctrlKey || ev.metaKey) { window.open(link.href, "_blank"); } else { window.location.href = link.href; }
        });
    });
})();
