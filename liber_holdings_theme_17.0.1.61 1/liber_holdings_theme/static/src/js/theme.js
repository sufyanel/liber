/** @odoo-module **/

/**
 * Liber Holdings theme — sticky header + left shop filters rail (desktop).
 *
 * Desktop: filters sit in-flow on the left of the product grid (header untouched).
 * Mobile: Bootstrap offcanvas from the left, opened via the Filters button.
 *
 * Important: on desktop we strip data-bs-toggle/dismiss so Bootstrap's Offcanvas
 * data-api never initializes against the rail element (that caused parentNode errors).
 */
import publicWidget from "@web/legacy/js/public/public_widget";

const FILTERS_PREF_KEY = "liber_shop_filters_open";

function isDesktop() {
    return window.matchMedia("(min-width: 992px)").matches;
}

function getFiltersPref() {
    const v = sessionStorage.getItem(FILTERS_PREF_KEY);
    if (v === null) {
        return true; // open by default on desktop
    }
    return v === "1";
}

function setFiltersPref(open) {
    sessionStorage.setItem(FILTERS_PREF_KEY, open ? "1" : "0");
}

publicWidget.registry.liberStickyHeader = publicWidget.Widget.extend({
    selector: "html[data-liber-theme] header, .o_liber_header",

    start() {
        const onScroll = () => {
            this.el.classList.toggle("o_liber_header_scrolled", window.scrollY > 8);
        };
        window.addEventListener("scroll", onScroll, {passive: true});
        onScroll();
        return this._super(...arguments);
    },
});

publicWidget.registry.liberShopFiltersRail = publicWidget.Widget.extend({
    selector: ".o_wsale_products_page",
    events: {
        "click .o_liber_filters_toggle": "_onToggleClick",
        "click #o_wsale_offcanvas .btn-close": "_onCloseClick",
    },

    start() {
        this.drawer = this.el.querySelector("#o_wsale_offcanvas.o_liber_filters_drawer");
        this.row = this.el.querySelector(".o_wsale_products_main_row");
        this.grid = this.el.querySelector("#products_grid");
        this.homeParent = this.drawer && this.drawer.parentElement;
        this.homeNext = this.drawer && this.drawer.nextSibling;

        // Mark filter buttons so we can bind without relying on data-bs-toggle
        this.el.querySelectorAll('[data-bs-target="#o_wsale_offcanvas"]').forEach((btn) => {
            btn.classList.add("o_liber_filters_toggle");
        });

        this._onResize = () => this._syncMode();
        window.addEventListener("resize", this._onResize, {passive: true});
        this._syncMode();

        return this._super(...arguments);
    },

    destroy() {
        window.removeEventListener("resize", this._onResize);
        this._enableBootstrapOffcanvasApi();
        return this._super(...arguments);
    },

    _syncMode() {
        if (!this.drawer || !this.row || !this.grid) {
            return;
        }
        if (isDesktop()) {
            this._enterRailMode();
        } else {
            this._enterOffcanvasMode();
        }
    },

    _disposeOffcanvas() {
        const OffcanvasCls = window.Offcanvas;
        if (!OffcanvasCls || !this.drawer) {
            return;
        }
        const inst = OffcanvasCls.getInstance(this.drawer);
        if (inst) {
            inst.dispose();
        }
    },

    /**
     * Prevent Bootstrap Offcanvas data-api from touching the rail element.
     */
    _disableBootstrapOffcanvasApi() {
        this.el.querySelectorAll(".o_liber_filters_toggle, [data-bs-target='#o_wsale_offcanvas']").forEach((btn) => {
            btn.classList.add("o_liber_filters_toggle");
            if (btn.hasAttribute("data-bs-toggle")) {
                btn.dataset.liberBsToggle = btn.getAttribute("data-bs-toggle");
                btn.removeAttribute("data-bs-toggle");
            }
        });
        const closeBtn = this.drawer && this.drawer.querySelector(".btn-close");
        if (closeBtn && closeBtn.hasAttribute("data-bs-dismiss")) {
            closeBtn.dataset.liberBsDismiss = closeBtn.getAttribute("data-bs-dismiss");
            closeBtn.removeAttribute("data-bs-dismiss");
        }
    },

    _enableBootstrapOffcanvasApi() {
        this.el.querySelectorAll(".o_liber_filters_toggle").forEach((btn) => {
            if (btn.dataset.liberBsToggle) {
                btn.setAttribute("data-bs-toggle", btn.dataset.liberBsToggle);
                delete btn.dataset.liberBsToggle;
            } else if (!btn.hasAttribute("data-bs-toggle")) {
                btn.setAttribute("data-bs-toggle", "offcanvas");
            }
            if (!btn.hasAttribute("data-bs-target")) {
                btn.setAttribute("data-bs-target", "#o_wsale_offcanvas");
            }
        });
        const closeBtn = this.drawer && this.drawer.querySelector(".btn-close");
        if (closeBtn) {
            if (closeBtn.dataset.liberBsDismiss) {
                closeBtn.setAttribute("data-bs-dismiss", closeBtn.dataset.liberBsDismiss);
                delete closeBtn.dataset.liberBsDismiss;
            } else if (!closeBtn.hasAttribute("data-bs-dismiss")) {
                closeBtn.setAttribute("data-bs-dismiss", "offcanvas");
            }
        }
    },

    _enterRailMode() {
        this._disposeOffcanvas();
        this._disableBootstrapOffcanvasApi();

        this.drawer.classList.remove(
            "offcanvas",
            "offcanvas-start",
            "offcanvas-end",
            "show",
            "showing",
            "hiding"
        );
        this.drawer.classList.add("o_liber_shop_filters_rail");
        this.drawer.style.removeProperty("visibility");
        this.drawer.style.removeProperty("transform");

        if (this.drawer.parentElement !== this.row) {
            this.row.insertBefore(this.drawer, this.grid);
        }

        document.body.classList.remove("o_liber_filters_open");
        if (getFiltersPref()) {
            this._openRail(false);
        } else {
            this._closeRail(false);
        }
    },

    _enterOffcanvasMode() {
        if (this.homeParent && this.drawer.parentElement !== this.homeParent) {
            if (this.homeNext && this.homeNext.parentElement === this.homeParent) {
                this.homeParent.insertBefore(this.drawer, this.homeNext);
            } else {
                this.homeParent.appendChild(this.drawer);
            }
        }

        this.drawer.classList.remove(
            "o_liber_shop_filters_rail",
            "o_liber_rail_open",
            "o_liber_rail_collapsed",
            "col-3",
            "d-none",
            "d-lg-block"
        );
        this.drawer.classList.add("offcanvas", "offcanvas-start");
        this.grid.classList.remove("col-lg-9", "o_liber_grid_with_filters");
        if (!this.grid.classList.contains("col-12")) {
            this.grid.classList.add("col-12");
        }
        document.body.classList.remove("o_liber_filters_open", "o_liber_filters_rail_open");
        this._enableBootstrapOffcanvasApi();
    },

    _openRail(persist = true) {
        this.drawer.classList.remove("d-none", "o_liber_rail_collapsed");
        this.drawer.classList.add("o_liber_rail_open");
        this.grid.classList.add("o_liber_grid_with_filters");
        this.grid.classList.remove("col-12");
        document.body.classList.add("o_liber_filters_rail_open");
        if (persist) {
            setFiltersPref(true);
        }
    },

    _closeRail(persist = true) {
        this.drawer.classList.add("d-none", "o_liber_rail_collapsed");
        this.drawer.classList.remove("o_liber_rail_open", "col-3");
        this.grid.classList.remove("o_liber_grid_with_filters", "col-lg-9");
        this.grid.classList.add("col-12");
        document.body.classList.remove("o_liber_filters_rail_open");
        if (persist) {
            setFiltersPref(false);
        }
    },

    _onToggleClick(ev) {
        if (!isDesktop() || !this.drawer) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        if (this.drawer.classList.contains("d-none") || this.drawer.classList.contains("o_liber_rail_collapsed")) {
            this._openRail();
        } else {
            this._closeRail();
        }
    },

    _onCloseClick(ev) {
        if (!isDesktop()) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        this._closeRail();
    },
});


/* ============================================================
   17.0.1.31 - open a product or blog row by clicking anywhere on it.
   Links, buttons and form controls keep their own behaviour,
   Ctrl or Cmd click opens a new tab, and selecting text does nothing.
   ============================================================ */
(function () {
    "use strict";

    function liberBindRowClicks() {
        if (!document.documentElement.hasAttribute("data-liber-theme")) {
            return;
        }
        var selectors = [
            ".o_wsale_products_grid_table_wrapper tr",
            ".oe_product",
            ".o_liber_product_card",
            ".o_wblog_post",
            "article.o_wblog_post_short"
        ];
        selectors.forEach(function (selector) {
            document.querySelectorAll(selector).forEach(function (row) {
                if (row.dataset.liberRowBound) {
                    return;
                }
                var link = row.querySelector('a[href^="/shop/"], a[href^="/blog/"]');
                if (!link) {
                    return;
                }
                row.dataset.liberRowBound = "1";
                row.classList.add("o_liber_clickable");
                row.addEventListener("click", function (ev) {
                    if (ev.target.closest("a, button, input, select, textarea, label, .o_liber_no_row_click")) {
                        return;
                    }
                    if (String(window.getSelection())) {
                        return;
                    }
                    if (ev.ctrlKey || ev.metaKey || ev.button === 1) {
                        window.open(link.getAttribute("href"), "_blank");
                    } else {
                        window.location.href = link.getAttribute("href");
                    }
                });
            });
        });
    }

    if (document.readyState !== "loading") {
        liberBindRowClicks();
    } else {
        document.addEventListener("DOMContentLoaded", liberBindRowClicks);
    }
    document.addEventListener("shop_products_updated", liberBindRowClicks);
})();


/* 17.0.1.37 - panels fade in as they come into view. Does nothing when the
   visitor has asked for reduced motion, and nothing on browsers without
   IntersectionObserver, where everything simply shows as normal. */
(function () {
    "use strict";
    function liberReveal() {
        var root = document.documentElement;
        if (!root.hasAttribute("data-liber-theme")) { return; }
        if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) { return; }
        if (!("IntersectionObserver" in window)) { return; }
        var targets = document.querySelectorAll(
            ".o_liber_pdp_spec_table_card, .o_liber_product_card, .o_liber_brand_card, #wrap section"
        );
        if (!targets.length) { return; }
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-in");
                    io.unobserve(entry.target);
                }
            });
        }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
        targets.forEach(function (el, i) {
            if (i > 60) { return; }          // long catalogue pages stay snappy
            el.classList.add("o_liber_reveal");
            io.observe(el);
        });
    }
    if (document.readyState !== "loading") { liberReveal(); }
    else { document.addEventListener("DOMContentLoaded", liberReveal); }
})();

/* Liber catalog (view-only): value search in long filter groups, row / card click opens the product,
   and on the product page the spec table and Variant Sales Description follow the selected variant. */
(function () {
    "use strict";
    function norm(s) { return (s || "").toLowerCase().replace(/\s+/g, " ").trim(); }
    function ready(fn) { if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", fn); } else { fn(); } }
    ready(function () {
        if (document.documentElement.getAttribute("data-liber-theme") !== "1") { return; }
        Array.prototype.forEach.call(document.querySelectorAll(".lcat-value-search"), function (box) {
            box.addEventListener("input", function () {
                var q = norm(box.value);
                Array.prototype.forEach.call(box.parentElement.querySelectorAll(".lcat-check"), function (l) {
                    l.classList.toggle("lcat-qf-hide", !(!q || norm(l.textContent).indexOf(q) !== -1));
                });
            });
            box.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); } });
        });
        var grid = document.getElementById("products_grid");
        if (grid) {
            grid.addEventListener("click", function (ev) {
                var row = ev.target.closest(".lcat-table tbody tr, .lcat-pcard");
                if (!row || ev.target.closest("a, button, input, label, form")) { return; }
                if (window.getSelection && String(window.getSelection()).length) { return; }
                var link = row.querySelector(".lcat-pname, .lcat-part");
                if (!link) { return; }
                if (ev.ctrlKey || ev.metaKey) { window.open(link.href, "_blank"); } else { window.location.href = link.href; }
            });
        }
        var variants = document.querySelectorAll(".lcat-spec-variant");
        var descBox = document.querySelector(".lcat-variant-desc");
        if (!variants.length && !descBox) { return; }
        var all = document.querySelector(".lcat-spec-all");
        var last = null;
        function sync() {
            var input = document.querySelector("#product_details input.product_id, #product_details input[name='product_id']");
            var id = input ? String(input.value || "") : "";
            if (id === last) { return; }
            last = id;
            var shown = false;
            Array.prototype.forEach.call(variants, function (t) {
                var on = t.getAttribute("data-variant") === id;
                t.style.display = on ? "" : "none";
                shown = shown || on;
            });
            if (all) { all.classList.toggle("lcat-has-variant", shown); }
            if (descBox) {
                var src = document.querySelector('.lcat-variant-data [data-variant-desc="' + id + '"]');
                if (src) { descBox.innerHTML = src.innerHTML; descBox.style.display = ""; }
                else if (variants.length) { descBox.style.display = "none"; }
            }
        }
        sync();
        window.setInterval(sync, 400);
    });
})();

/* Liber product page: precise image magnifier (same behaviour as RBC: 2.6x panel beside the image).
   Finds the product image under the pointer by position, so overlays (wishlist, ribbons, Odoo's image layer),
   re-rendered variant images and touch-capable laptops do not stop it. Mouse / pen only. */
(function () {
    "use strict";
    if (window.__lcatZoom) { return; } window.__lcatZoom = true;
    var SEL = "#o-carousel-product img, #o-grid-product img, .o_wsale_product_images img, .o_wsale_product_page .product_detail_img";
    var flyout = null, current = null;
    function bigSrc(img) {
        var s = img.dataset.zoomImage || img.getAttribute("data-zoom-image") || img.currentSrc || img.src || "";
        return s.replace(/image_(128|256|512|1024)/, "image_1920");
    }
    function usable(img) {
        var src = img.currentSrc || img.src || "";
        if (!src || /placeholder|\/web\/static\/img\//.test(src)) { return false; }
        if (img.closest(".carousel-indicators, .o_carousel_product_indicators")) { return false; }   // thumbnails
        var r = img.getBoundingClientRect();
        return r.width > 120 && r.height > 120;
    }
    function imageAt(x, y) {
        var imgs = document.querySelectorAll(SEL);
        for (var i = 0; i < imgs.length; i++) {
            var img = imgs[i];
            if (!img.offsetParent || !usable(img)) { continue; }
            var r = img.getBoundingClientRect();
            if (x >= r.left && x <= r.right && y >= r.top && y <= r.bottom) { return img; }
        }
        return null;
    }
    function close() { if (flyout) { flyout.remove(); flyout = null; } current = null; }
    function open(img) {
        close();
        current = img;
        var r = img.getBoundingClientRect();
        flyout = document.createElement("div");
        flyout.className = "lcat-zoom-flyout";
        var size = Math.min(Math.max(r.width, 360), 560);
        flyout.style.width = size + "px";
        flyout.style.height = size + "px";
        flyout.style.backgroundImage = 'url("' + bigSrc(img) + '")';
        flyout.style.backgroundRepeat = "no-repeat";
        document.body.appendChild(flyout);
    }
    function place(x, y) {
        var r = current.getBoundingClientRect();
        var px = Math.min(Math.max(x - r.left, 0), r.width), py = Math.min(Math.max(y - r.top, 0), r.height);
        var zoom = 2.6, fw = flyout.offsetWidth, fh = flyout.offsetHeight, bw = r.width * zoom, bh = r.height * zoom;
        flyout.style.backgroundSize = bw + "px " + bh + "px";
        var bx = Math.min(Math.max(px * zoom - fw / 2, 0), Math.max(bw - fw, 0));
        var by = Math.min(Math.max(py * zoom - fh / 2, 0), Math.max(bh - fh, 0));
        flyout.style.backgroundPosition = (-bx) + "px " + (-by) + "px";
        var left = r.right + 16;
        if (left + fw > window.innerWidth - 8) { left = Math.max(r.left - fw - 16, 8); }
        flyout.style.left = left + "px";
        flyout.style.top = Math.min(Math.max(r.top, 8), window.innerHeight - fh - 8) + "px";
    }
    function onMove(ev) {
        if (ev.pointerType && ev.pointerType === "touch") { return; }
        var img = imageAt(ev.clientX, ev.clientY);
        if (!img) { close(); return; }
        if (img !== current) { open(img); }
        place(ev.clientX, ev.clientY);
    }
    function start() {
        if (document.documentElement.getAttribute("data-liber-theme") !== "1") { return; }
        if (!document.querySelector(".o_wsale_product_page, #product_detail")) { return; }
        document.addEventListener(window.PointerEvent ? "pointermove" : "mousemove", onMove, { passive: true });
        document.addEventListener("mouseleave", close);
        window.addEventListener("scroll", close, { passive: true });
        window.addEventListener("blur", close);
    }
    if (document.readyState === "loading") { document.addEventListener("DOMContentLoaded", start); } else { start(); }
})();
