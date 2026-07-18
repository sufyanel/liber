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
