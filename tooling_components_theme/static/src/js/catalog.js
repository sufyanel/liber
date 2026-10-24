/* Tooling Components catalog helpers (plain script, TC website only):
 *  - search bar: mockup placeholder + instant filtering of the rows on the page
 *    (Enter still runs Odoo's full catalog search);
 *  - "search values" boxes inside long filter groups. */
(function () {
    "use strict";
    function norm(s) { return (s || "").toLowerCase().replace(/\s+/g, " ").trim(); }
    function init() {
        if (document.documentElement.getAttribute("data-tc-theme") !== "1") { return; }
        var grid = document.getElementById("products_grid");
        if (!grid) { return; }
        var input = grid.querySelector(".products_header input[name='search']");
        var status = grid.querySelector(".tc-qf-status");
        if (input) {
            input.setAttribute("placeholder", "Search the full catalog by part number, brand or spec \u2014 e.g. 6205, SKF, 25 mm\u2026");
            // suggestions come from Odoo's own dropdown; the catalog only changes
            // when the user presses Enter or picks a suggestion.
        }

        Array.prototype.forEach.call(document.querySelectorAll(".tc-value-search"), function (box) {
            box.addEventListener("input", function () {
                var q = norm(box.value);
                var labels = box.parentElement.querySelectorAll(".tc-check");
                Array.prototype.forEach.call(labels, function (l) {
                    l.classList.toggle("tc-qf-hide", !(!q || norm(l.textContent).indexOf(q) !== -1));
                });
            });
            box.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); } });
        });
    }
    function toast(text, ok) {
        var t = document.createElement("div");
        t.className = "tc-toast" + (ok ? "" : " err");
        t.textContent = text;
        document.body.appendChild(t);
        setTimeout(function () { t.classList.add("show"); }, 10);
        setTimeout(function () { t.classList.remove("show"); setTimeout(function () { t.remove(); }, 300); }, 2600);
    }
    function initCart() {
        if (document.documentElement.getAttribute("data-tc-theme") !== "1") { return; }
        document.addEventListener("submit", function (ev) {
            var form = ev.target;
            if (!form.matches || !form.matches(".tc-actions form")) { return; }
            ev.preventDefault();
            var input = form.querySelector("input[name='product_id']");
            var btn = form.querySelector("button");
            if (!input) { return; }
            if (btn) { btn.classList.add("tc-busy"); }
            var badges = document.querySelectorAll(".tc-cart-qty, .my_cart_quantity");
            Array.prototype.forEach.call(badges, function (el) {
                el.textContent = (parseInt(el.textContent, 10) || 0) + 1;   // optimistic
            });
            toast("Adding to cart\u2026", true);
            fetch("/shop/cart/update_json", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: { product_id: parseInt(input.value, 10), add_qty: 1, display: false } }),
            }).then(function (r) { return r.json(); }).then(function (data) {
                var res = data && data.result;
                if (res && typeof res.cart_quantity !== "undefined") {
                    Array.prototype.forEach.call(document.querySelectorAll(".tc-cart-qty, .my_cart_quantity"), function (el) {
                        el.textContent = res.cart_quantity;
                    });
                    toast("Added to cart", true);
                } else {
                    toast("Could not add this item - open the product page", false);
                }
            }).catch(function () {
                toast("Could not add this item - open the product page", false);
            }).then(function () { if (btn) { btn.classList.remove("tc-busy"); } });
        });
    }

    /* ---- precise image magnifier (replaces Odoo's flyout) ---- */
    function initZoom(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        var wrap = document.querySelector(".o_wsale_product_images");
        if (!wrap) { return; }
        var lens = null, flyout = null, current = null;
        function bigSrc(img) {
            var s = img.dataset.zoomImage || img.getAttribute("data-zoom-image") || img.currentSrc || img.src;
            return s.replace(/image_(128|256|512|1024)/, "image_1920");
        }
        function close() {
            if (flyout) { flyout.remove(); flyout = null; }
            if (lens) { lens.remove(); lens = null; }
            current = null;
        }
        function open(img) {
            close();
            current = img;
            var r = img.getBoundingClientRect();
            flyout = document.createElement("div");
            flyout.className = pre + "-zoom-flyout";
            var size = Math.min(Math.max(r.width, 360), 560);
            flyout.style.width = size + "px";
            flyout.style.height = size + "px";
            flyout.style.backgroundImage = 'url("' + bigSrc(img) + '")';
            flyout.style.backgroundRepeat = "no-repeat";
            document.body.appendChild(flyout);
            lens = null;
        }
        function move(ev) {
            if (!current || !flyout) { return; }
            var r = current.getBoundingClientRect();
            var x = Math.min(Math.max(ev.clientX - r.left, 0), r.width);
            var y = Math.min(Math.max(ev.clientY - r.top, 0), r.height);
            var zoom = 2.6;                                   // magnification
            var fw = flyout.offsetWidth, fh = flyout.offsetHeight;
            var bw = r.width * zoom, bh = r.height * zoom;    // zoomed image size
            flyout.style.backgroundSize = bw + "px " + bh + "px";
            var bx = Math.min(Math.max(x * zoom - fw / 2, 0), Math.max(bw - fw, 0));
            var by = Math.min(Math.max(y * zoom - fh / 2, 0), Math.max(bh - fh, 0));
            flyout.style.backgroundPosition = (-bx) + "px " + (-by) + "px";
            // place the panel beside the image, inside the viewport
            var left = r.right + 16;
            if (left + fw > window.innerWidth - 8) { left = Math.max(r.left - fw - 16, 8); }
            var top = Math.min(Math.max(r.top, 8), window.innerHeight - fh - 8);
            flyout.style.left = left + "px";
            flyout.style.top = top + "px";

        }
        wrap.addEventListener("mouseover", function (ev) {
            var img = ev.target.closest("img");
            if (img && wrap.contains(img) && img !== current) { open(img); move(ev); }
        });
        wrap.addEventListener("mousemove", move);
        wrap.addEventListener("mouseleave", close);
        // safety net: close as soon as the pointer is outside the image itself
        document.addEventListener("mousemove", function (ev) {
            if (!current) { return; }
            var r = current.getBoundingClientRect();
            if (ev.clientX < r.left || ev.clientX > r.right || ev.clientY < r.top || ev.clientY > r.bottom) { close(); }
        });
        document.addEventListener("mouseleave", close);
        window.addEventListener("scroll", close, { passive: true });
    }

    /* ---- fast language switch: remember the choice and go straight to the page ---- */
    function initLangSwitch(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        var links = document.querySelectorAll("." + pre + "-lang-link");
        var done = {};
        function prefetch(href) {
            if (done[href]) { return; }
            done[href] = true;
            var l = document.createElement("link");
            l.rel = "prefetch"; l.href = href; l.as = "document";
            document.head.appendChild(l);
        }
        Array.prototype.forEach.call(links, function (a) {
            ["mouseenter", "focus", "touchstart"].forEach(function (evt) {
                a.addEventListener(evt, function () { if (!a.classList.contains("active")) { prefetch(a.href); } }, { passive: true });
            });
        });
        window.addEventListener("pageshow", function () { document.documentElement.classList.remove(pre + "-nav-loading"); });
    }


    /* ---- product page quantity: left button = minus, right button = plus ----
       Odoo decides the direction by looking for a .fa-minus icon inside the button;
       when another module changes those icons every click counts as "plus". */
    function initQty(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        document.addEventListener("click", function (ev) {
            var a = ev.target.closest && ev.target.closest(".css_quantity a.js_add_cart_json");
            if (!a) { return; }
            var group = a.closest(".css_quantity");
            if (!group) { return; }
            var input = group.querySelector("input");
            if (!input) { return; }
            ev.preventDefault();
            ev.stopImmediatePropagation();
            var links = group.querySelectorAll("a.js_add_cart_json");
            var step = (a === links[0]) ? -1 : 1;
            var inCart = !group.closest("#product_details");
            var min = parseFloat(input.getAttribute("data-min") || (inCart ? "0" : "1"));
            var max = parseFloat(input.getAttribute("data-max") || "Infinity");
            var val = (parseFloat(input.value) || min) + step;
            val = Math.max(min, Math.min(max, val));
            input.value = val;
            input.dispatchEvent(new Event("change", { bubbles: true }));
        }, true);
    }

    /* ---- whole product card opens the product ---- */
    function initCards(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        document.addEventListener("click", function (ev) {
            var card = ev.target.closest && (ev.target.closest("." + pre + "-pcard") || ev.target.closest("." + pre + "-table tbody tr") || ev.target.closest("." + pre + "-kb-row"));
            if (!card || ev.target.closest("a, button, form, input, select, label")) { return; }
            if (window.getSelection && String(window.getSelection()).length) { return; }   // the visitor is selecting text
            var link = card.querySelector("." + pre + "-pname, ." + pre + "-pcard-img, h3 a, ." + pre + "-kb-thumb");
            if (link && link.getAttribute("href")) {
                if (ev.ctrlKey || ev.metaKey) { window.open(link.href, "_blank"); } else { window.location.href = link.href; }
            }
        });
    }

    /* ---- variant description and spec table follow the selected variant.
       The product Sales Description always stays visible; the Variant Sales Description is shown below it. ---- */
    function initVariants(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        var holder = document.querySelector("." + pre + "-variant-data");
        if (!holder) { return; }
        var input = document.querySelector("#product_details input.product_id");
        var last = null;
        function apply() {
            var vid = input ? String(input.value) : "";
            if (vid === last) { return; }
            last = vid;
            var desc = holder.querySelector("[data-variant-desc='" + vid + "']");
            var box = document.querySelector("." + pre + "-variant-desc");
            if (box) { box.innerHTML = desc ? desc.innerHTML : ""; box.style.display = desc ? "" : "none"; }
            var tables = document.querySelectorAll("." + pre + "-spec-variant");
            var matched = false;
            Array.prototype.forEach.call(tables, function (t) {
                var on = t.getAttribute("data-variant") === vid;
                t.style.display = on ? "" : "none";
                matched = matched || on;
            });
            var generic = document.querySelector("." + pre + "-spec-table:not(." + pre + "-spec-variant)");
            if (generic && tables.length) { generic.style.display = matched ? "none" : ""; }
        }
        apply();
        setInterval(apply, 300);
    }

    /* ---- show the long description once: hide any other block with the same text ---- */
    function initDedupe(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        var ours = document.querySelector("." + pre + "-long-desc");
        var area = document.querySelector("#product_details") || document.querySelector("#product_detail");
        if (!ours || !area) { return; }
        var norm = function (t) { return (t || "").replace(/\s+/g, " ").trim(); };
        var text = norm(ours.textContent);
        if (text.length < 40) { return; }
        Array.prototype.forEach.call(area.querySelectorAll("div, p, section"), function (el) {
            if (el === ours || ours.contains(el) || el.contains(ours)) { return; }
            if (norm(el.textContent) === text) { el.style.display = "none"; el.setAttribute("data-" + pre + "-dup", "1"); }
        });
    }

    /* ---- faster navigation: start loading a page when the visitor hovers or touches its link ---- */
    function initPrefetch(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        var done = {};
        var SKIP = /^\/(web|odoo|shop\/cart|shop\/checkout|shop\/payment|shop\/confirmation|my|logout|website\/lang)(\/|$|\?)/;
        function candidate(a) {
            if (!a || !a.href || a.target === "_blank" || a.hasAttribute("download")) { return false; }
            var u;
            try { u = new URL(a.href, location.href); } catch (e) { return false; }
            if (u.origin !== location.origin || u.hash && u.pathname === location.pathname) { return false; }
            if (SKIP.test(u.pathname) || /\.(pdf|zip|png|jpe?g|webp|svg)$/i.test(u.pathname)) { return false; }
            return u.href;
        }
        var conn = navigator.connection || {};
        if (conn.saveData || /2g/.test(conn.effectiveType || "")) { return; }
        var count = 0;
        function prefetch(ev) {
            var a = ev.target.closest && ev.target.closest("a");
            var href = candidate(a);
            if (!href || done[href] || count >= 4) { return; }
            done[href] = true; count++;
            var l = document.createElement("link");
            l.rel = "prefetch"; l.href = href; l.as = "document";
            document.head.appendChild(l);
        }
        document.addEventListener("mouseover", function (ev) {
            var a = ev.target.closest && ev.target.closest("a");
            if (!a) { return; }
            var t = setTimeout(function () { prefetch(ev); }, 200);   // ignore links the pointer only passes over
            a.addEventListener("mouseleave", function () { clearTimeout(t); }, { once: true });
        }, { passive: true });
        document.addEventListener("touchstart", prefetch, { passive: true });
    }

    /* ---- blog thumbnails: replace missing, blank or icon-sized pictures with the brief header ---- */
    function initBlogThumbs(pre) {
        if (document.documentElement.getAttribute("data-" + pre + "-theme") !== "1") { return; }
        function fallback(img) { var a = img.closest("." + pre + "-kb-thumb"); if (a) { a.classList.add(pre + "-kb-thumb-fallback"); } }
        function blank(img) {
            try {
                var c = document.createElement("canvas"); c.width = 8; c.height = 8;
                var x = c.getContext("2d"); x.drawImage(img, 0, 0, 8, 8);
                var d = x.getImageData(0, 0, 8, 8).data, min = 255, max = 0;
                for (var i = 0; i < d.length; i += 4) {
                    var v = (d[i] + d[i + 1] + d[i + 2]) / 3 * (d[i + 3] / 255) + 255 * (1 - d[i + 3] / 255);
                    if (v < min) { min = v; } if (v > max) { max = v; }
                }
                return max - min < 12;                                   // one flat colour: an empty cover
            } catch (e) { return false; }                               // other-site image: cannot inspect, keep it
        }
        function check(img) {
            if (/placeholder|default_image|s_default|image_placeholder/i.test(img.getAttribute("src") || "")) { return fallback(img); }
            if (!img.naturalWidth || img.naturalWidth < 60 || img.naturalHeight < 40 || blank(img)) { fallback(img); }
        }
        Array.prototype.forEach.call(document.querySelectorAll("." + pre + "-kb-thumb-img"), function (img) {
            img.loading = "eager";
            if (img.complete) { check(img); }
            else { img.addEventListener("load", function () { check(img); }); img.addEventListener("error", function () { fallback(img); }); }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function () { init(); initCart(); initZoom("tc"); initLangSwitch("tc"); initQty("tc"); initCards("tc"); initVariants("tc"); initDedupe("tc"); initPrefetch("tc"); initBlogThumbs("tc"); });
    } else { init(); initCart(); initZoom("tc"); initLangSwitch("tc"); initQty("tc"); initCards("tc"); initVariants("tc"); initDedupe("tc"); initPrefetch("tc"); initBlogThumbs("tc"); }
})();
