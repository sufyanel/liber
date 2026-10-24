/** @odoo-module **/
/* Invoice Comparison Dashboard - Axiom World
 * Built like the Threshold Dashboard: one dashboard per company and year,
 * Q1-Q4 / FY / custom range tabs, KPI cards, charts and a drill-down table. */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { useSetupAction } from "@web/webclient/actions/action_hook";
import { Component, useState, useRef, onWillStart, onMounted, onPatched, onWillUnmount } from "@odoo/owl";

const C = {
    navy: "#13294B", teal: "#0E7C86", sky: "#5FB3BA", amber: "#E0892B",
    amberSoft: "rgba(224,137,43,0.18)", green: "#15803D", red: "#C2410C",
    slate: "#64748B", grid: "rgba(100,116,139,0.15)", light: "#CBD5E1",
};
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const WINDOW_MONTHS = {
    Q1: [1, 2, 3], Q2: [4, 5, 6], Q3: [7, 8, 9], Q4: [10, 11, 12],
    FY: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], CUSTOM: [0],
};

export class InvoiceComparisonDashboard extends Component {
    static template = "x_invcmp_dashboard.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.params = (this.props.action && this.props.action.params) || {};
        this.state = useState({
            loading: true, refreshing: false, applying: false, downloading: false,
            dashboards: [], dashboardId: null, dashboard: null,
            periods: [], customers: [], selectedCode: null, customFrom: "", customTo: "",
        });
        this.index = {};
        // come back from a drill-down to the same dashboard and tab
        const saved = this.props.state || {};
        this.state.dashboardId = saved.dashboardId || null;
        this.state.selectedCode = saved.selectedCode || null;
        useSetupAction({
            getLocalState: () => ({ dashboardId: this.state.dashboardId, selectedCode: this.state.selectedCode }),
        });
        this.refs = {
            years: useRef("years"), months: useRef("months"), top: useRef("top"),
            bridge: useRef("bridge"), mix: useRef("mix"),
        };
        this.charts = {};
        this.chartKey = null;
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadDashboards();
        });
        onMounted(() => this.renderChartsIfNeeded());
        onPatched(() => this.renderChartsIfNeeded());
        onWillUnmount(() => this.destroyCharts());
    }

    // ------------------------------------------------------------ data
    async loadDashboards() {
        const dashboards = await this.orm.searchRead("x_invcmp_dashboard", [],
            ["x_name", "x_company_id", "x_year", "x_years_count", "x_peer_company_ids",
             "x_include_refunds", "x_currency_code", "x_refreshed", "x_custom_from", "x_custom_to"],
            { order: "x_year desc, id" });
        this.state.dashboards = dashboards;
        if (!dashboards.length) {
            this.state.loading = false;
            return;
        }
        const keep = dashboards.find((d) => d.id === this.state.dashboardId);
        await this.selectDashboard((keep || dashboards[0]).id);
    }

    async selectDashboard(id) {
        this.state.loading = true;
        this.state.dashboardId = id;
        this.state.dashboard = this.state.dashboards.find((d) => d.id === id);
        const [periods, customers, cells] = await Promise.all([
            this.orm.searchRead("x_invcmp_period", [["x_dashboard_id", "=", id]],
                ["x_name", "x_code", "x_sequence", "x_date_from", "x_date_to", "x_is_future",
                 "x_is_year", "x_is_custom", "x_invoiced", "x_budget", "x_total", "x_prev_total",
                 "x_customers", "x_new_customers", "x_lost_customers"], { order: "x_sequence, id" }),
            this.orm.searchRead("x_invcmp_customer", [["x_dashboard_id", "=", id]],
                ["x_name", "x_partner_id", "x_partner_ids", "x_sequence", "x_is_new", "x_is_lost"],
                { order: "x_sequence, id" }),
            this.orm.searchRead("x_invcmp_cell", [["x_dashboard_id", "=", id]],
                ["x_customer_id", "x_year", "x_month", "x_invoiced", "x_budget"]),
        ]);
        this.state.periods = periods;
        this.state.customers = customers;
        const index = {};
        for (const cell of cells) {
            const cid = cell.x_customer_id[0];
            index[cid] = index[cid] || {};
            index[cid][cell.x_year] = index[cid][cell.x_year] || {};
            index[cid][cell.x_year][cell.x_month] = { inv: cell.x_invoiced, bud: cell.x_budget };
        }
        this.index = index;
        const d = this.state.dashboard;
        // refresh quietly in the background when the snapshot is more than an hour old, so customers archived
        // (or added) during the day are reflected without waiting for the nightly refresh
        const refreshedAt = d.x_refreshed ? new Date(d.x_refreshed.replace(" ", "T") + "Z") : null;
        if (periods.length && (!refreshedAt || Date.now() - refreshedAt.getTime() > 3600 * 1000) && !this._staleRefreshDone) {
            this._staleRefreshDone = true;
            setTimeout(() => this.applyCustomRange(true), 0);
        }
        const today = new Date().toISOString().slice(0, 10);
        const yearEnd = `${d.x_year}-12-31`;
        this.state.customFrom = d.x_custom_from || `${d.x_year}-01-01`;
        this.state.customTo = d.x_custom_to || (today < yearEnd ? today : yearEnd);

        if (this.state.selectedCode === "CUSTOM" && periods.some((p) => p.x_is_custom)) {
            this.state.loading = false;
            this.chartKey = null;
            return;
        }
        const quarters = periods.filter((p) => !p.x_is_year && !p.x_is_future);
        const current = this.state.selectedCode &&
            periods.find((p) => p.x_code === this.state.selectedCode && !p.x_is_future && !p.x_is_custom);
        this.state.selectedCode = current ? current.x_code
            : (quarters.length ? quarters[quarters.length - 1].x_code : "FY");
        this.state.loading = false;
        this.chartKey = null;
    }

    async onDashboardChange(ev) {
        await this.selectDashboard(parseInt(ev.target.value));
    }

    selectPeriod(code) {
        this.state.selectedCode = code;
        // Custom: calculate straight away the first time (or when the stored range differs from the dates shown)
        if (code === "CUSTOM") {
            const d = this.state.dashboard || {};
            if (!this.customPeriod || d.x_custom_from !== this.state.customFrom || d.x_custom_to !== this.state.customTo) {
                this.applyCustomRange(true);
            }
        }
    }

    runContext(extra) {
        return Object.assign({
            active_model: "x_invcmp_dashboard",
            active_id: this.state.dashboardId,
            active_ids: [this.state.dashboardId],
        }, extra || {});
    }

    async refresh() {
        if (!this.params.refresh_action_id || !this.state.dashboardId) {
            return;
        }
        if (this.state.customFrom && this.state.customTo) {
            return this.applyCustomRange(false);
        }
        this.state.refreshing = true;
        try {
            await this.orm.call("ir.actions.server", "run", [[this.params.refresh_action_id]],
                { context: this.runContext() });
            await this.loadDashboards();
            this.notification.add("Dashboard refreshed", { type: "success" });
        } finally {
            this.state.refreshing = false;
        }
    }

    onDateChange() {
        // recalculate automatically shortly after the last change (no Calculate / Refresh click)
        clearTimeout(this._dateTimer);
        this._dateTimer = setTimeout(() => this.applyCustomRange(true), 600);
    }

    async applyCustomRange(silent) {
        const from = this.state.customFrom;
        const to = this.state.customTo;
        if (!from || !to || from > to) {
            this.notification.add("Choose a start date on or before the end date.", { type: "warning" });
            return;
        }
        if (this.state.applying) {
            this._pendingApply = true;   // run once more with the latest dates when the current one finishes
            return;
        }
        this.state.applying = true;
        try {
            await this.orm.write("x_invcmp_dashboard", [this.state.dashboardId],
                { x_custom_from: from, x_custom_to: to });
            await this.orm.call("ir.actions.server", "run", [[this.params.refresh_action_id]],
                { context: this.runContext() });
            const keep = this.state.selectedCode;
            await this.loadDashboards();
            this.state.selectedCode = keep || "CUSTOM";   // a background refresh keeps the tab the user is on
            if (!silent) {
                this.notification.add(`Calculated ${from} to ${to} for every year`, { type: "success" });
            }
        } finally {
            this.state.applying = false;
            if (this._pendingApply) {
                this._pendingApply = false;
                this.applyCustomRange(true);
            }
        }
    }

    async download() {
        if (!this.params.export_action_id || !this.state.dashboardId) {
            return;
        }
        this.state.downloading = true;
        try {
            const result = await this.orm.call("ir.actions.server", "run",
                [[this.params.export_action_id]],
                { context: this.runContext({ invcmp_window: this.state.selectedCode }) });
            if (result) {
                await this.actionService.doAction(result);
            }
        } finally {
            this.state.downloading = false;
        }
    }

    openSettings() {
        if (this.params.settings_action_id) {
            this.actionService.doAction(this.params.settings_action_id);
        }
    }

    // ------------------------------------------------------------ drill-down
    // Every figure opens the records it adds up. The list is built on the server
    // by the same code that calculated the figure, so it always matches.
    get windowMonths() {
        return WINDOW_MONTHS[this.state.selectedCode] || WINDOW_MONTHS.FY;
    }

    async drillTo(spec) {
        if (!this.params.refresh_action_id || !this.state.dashboardId) {
            return;
        }
        const action = await this.orm.call("ir.actions.server", "run", [[this.params.refresh_action_id]],
            { context: this.runContext({ invcmp_drill: spec }) });
        if (action) {
            this.lastDrill = spec;
            await this.actionService.doAction(action);
        }
    }

    /** Invoices when the figure is all invoicing, the budget lines when it is all
     *  budget, and the month-by-month breakdown (with both) when it mixes them. */
    openFigure({ title, customers = null, years, months = null, inv = 0, bud = 0, groupBy = null }) {
        const spec = { title, years, months: months || this.windowMonths };
        if (customers) {
            spec.customer_ids = customers.map((c) => c.id);
        }
        if (groupBy) {
            spec.group_by = groupBy;
        }
        if (Math.abs(bud) < 0.005) {
            spec.kind = "invoices";
        } else if (Math.abs(inv) < 0.005) {
            spec.kind = "budget";
        } else {
            spec.kind = "cells";
        }
        return this.drillTo(spec);
    }

    openCells(title, customers, years, groupBy = null) {
        const spec = { kind: "cells", title, years, months: this.windowMonths };
        if (customers) {
            spec.customer_ids = customers.map((c) => c.id);
        }
        if (groupBy) {
            spec.group_by = groupBy;
        }
        return this.drillTo(spec);
    }

    openCustomers(title, customers) {
        return this.drillTo({ kind: "customers", title, customer_ids: customers.map((c) => c.id) });
    }

    sumFor(customers, year, part, months = null) {
        return customers.reduce((acc, c) => acc + this.value(c.id, year, part, months), 0);
    }

    openYear(year, part = null) {
        const all = this.state.customers;
        const inv = part === "bud" ? 0 : this.sumFor(all, year, "inv");
        const bud = part === "inv" ? 0 : this.sumFor(all, year, "bud");
        const what = part === "bud" ? "Budget to come" : part === "inv" ? "Invoiced" : "Total";
        return this.openFigure({ title: `${what} · ${this.windowLabel} ${year}`, years: [year], inv, bud });
    }

    openCustomer(row, year) {
        const inv = this.value(row.customer.id, year, "inv");
        const bud = this.value(row.customer.id, year, "bud");
        return this.openFigure({ title: `${row.customer.x_name} · ${this.windowLabel} ${year}`,
            customers: [row.customer], years: [year], inv, bud });
    }

    openCustomerBudget(row) {
        const year = this.state.dashboard.x_year;
        return this.drillTo({ kind: "budget", title: `${row.customer.x_name} · budget to come ${year}`,
            customer_ids: [row.customer.id], years: [year], months: this.windowMonths });
    }

    openTotalBudget() {
        const year = this.state.dashboard.x_year;
        return this.drillTo({ kind: "budget", title: `Budget to come · ${this.windowLabel} ${year}`,
            years: [year], months: this.windowMonths });
    }

    openCustomerRecord(row) {
        this.actionService.doAction({
            type: "ir.actions.act_window", name: row.customer.x_name, res_model: "x_invcmp_customer",
            res_id: row.customer.id, views: [[false, "form"]], target: "new",
        });
    }

    onKpiClick(k) {
        if (k.open) {
            k.open();
        }
    }

    clickable(handler) {
        // nearest element, not only a direct hit: a small bar next to large ones stays clickable
        return {
            interaction: { mode: "nearest", intersect: false },
            onHover: (evt, elements) => {
                evt.native.target.style.cursor = elements.length ? "pointer" : "default";
            },
            onClick: (evt, elements) => {
                if (elements.length) {
                    handler(elements[0].index, elements[0].datasetIndex);
                }
            },
        };
    }

    // ------------------------------------------------------------ getters
    get selected() {
        return this.state.periods.find((p) => p.x_code === this.state.selectedCode) || null;
    }
    get customPeriod() {
        return this.state.periods.find((p) => p.x_is_custom) || null;
    }
    get standardPeriods() {
        return this.state.periods.filter((p) => !p.x_is_custom);
    }
    get hasData() {
        return this.state.periods.length > 0;
    }
    get currency() {
        return (this.state.dashboard && this.state.dashboard.x_currency_code) || "USD";
    }
    get refreshedLabel() {
        const d = this.state.dashboard && this.state.dashboard.x_refreshed;
        return d ? d.replace("T", " ").slice(0, 16) + " UTC" : "never";
    }
    get years() {
        const d = this.state.dashboard;
        if (!d) {
            return [];
        }
        const count = d.x_years_count || 5;
        const out = [];
        for (let y = d.x_year - count + 1; y <= d.x_year; y++) {
            out.push(y);
        }
        return out;
    }
    get windowLabel() {
        const code = this.state.selectedCode;
        return code === "CUSTOM" ? "Custom range" : code === "FY" ? "Full year" : code;
    }

    value(customerId, year, part, onlyMonths = null) {
        const months = onlyMonths || WINDOW_MONTHS[this.state.selectedCode] || WINDOW_MONTHS.FY;
        const byYear = this.index[customerId] && this.index[customerId][year];
        if (!byYear) {
            return 0;
        }
        let total = 0;
        for (const m of months) {
            const cell = byYear[m];
            if (cell) {
                total += part === "inv" ? cell.inv : part === "bud" ? cell.bud : cell.inv + cell.bud;
            }
        }
        return total;
    }

    get rows() {
        const years = this.years;
        const last = years[years.length - 1];
        const rows = [];
        for (const customer of this.state.customers) {
            const values = years.map((y) => this.value(customer.id, y));
            if (!values.some((v) => v)) {
                continue;
            }
            const cells = values.map((v, i) => {
                const before = i ? values[i - 1] : 0;
                return {
                    year: years[i], text: this.fmt(v), negative: v < 0, value: v,
                    growth: i && before ? `${(((v - before) / Math.abs(before)) * 100).toFixed(1)}%` : (i ? "–" : null),
                    growthTone: i && before ? (v >= before ? "o_axd_growth_up" : "o_axd_growth_down") : "",
                };
            });
            rows.push({
                customer, cells, total: values[values.length - 1],
                prev: values.length > 1 ? values[values.length - 2] : 0,
                budget: this.value(customer.id, last, "bud"),
                isNew: values.length > 1 && !values[values.length - 2] && values[values.length - 1] > 0,
            });
        }
        rows.sort((a, b) => b.total - a.total || b.prev - a.prev);
        return rows;
    }

    get totals() {
        const rows = this.rows;
        const values = this.years.map((y) => rows.reduce((acc, r) => acc + this.value(r.customer.id, y), 0));
        return {
            cells: values.map((v, i) => ({
                year: this.years[i], text: this.fmt(v), value: v,
                growth: i && values[i - 1] ? `${(((v - values[i - 1]) / Math.abs(values[i - 1])) * 100).toFixed(1)}%` : (i ? "–" : null),
            })),
            budget: this.fmt(rows.reduce((acc, r) => acc + r.budget, 0)),
        };
    }

    get groups() {
        const rows = this.rows;
        const y = this.state.dashboard.x_year;
        const active = rows.filter((r) => Math.abs(r.total) >= 0.005);
        const fresh = rows.filter((r) => Math.abs(r.prev) < 0.005 && Math.abs(r.total) >= 0.005);
        const lapsed = rows.filter((r) => Math.abs(r.prev) >= 0.005 && Math.abs(r.total) < 0.005);
        const grew = rows.filter((r) => Math.abs(r.prev) >= 0.005 && Math.abs(r.total) >= 0.005 && r.total >= r.prev);
        const shrank = rows.filter((r) => Math.abs(r.prev) >= 0.005 && Math.abs(r.total) >= 0.005 && r.total < r.prev);
        const top5 = rows.slice(0, 5);
        const others = rows.slice(5);
        const c = (list) => list.map((r) => r.customer);
        return { y, rows, active: c(active), fresh: c(fresh), lapsed: c(lapsed), grew: c(grew), shrank: c(shrank),
                 top5: c(top5), others: c(others), all: c(rows) };
    }

    get kpis() {
        const p = this.selected;
        if (!p) {
            return [];
        }
        const g = this.groups;
        const y = g.y;
        const rows = g.rows;
        const all = rows.reduce((acc, r) => acc + r.total, 0);
        const before = rows.reduce((acc, r) => acc + r.prev, 0);
        const inv = this.sumFor(g.all, y, "inv");
        const bud = this.sumFor(g.all, y, "bud");
        const top5 = rows.slice(0, 5).reduce((acc, r) => acc + r.total, 0);
        const freshIds = new Set(g.fresh.map((c) => c.id));
        const newRevenue = rows.filter((r) => freshIds.has(r.customer.id)).reduce((acc, r) => acc + r.total, 0);
        const growth = before ? ((all - before) / Math.abs(before)) * 100 : null;
        const delta = (value, prior) => {
            const diff = (value || 0) - (prior || 0);
            if (Math.abs(diff) < 0.5) {
                return { text: "no change vs last year", tone: "flat", arrow: "→" };
            }
            return { text: `${this.fmt(Math.abs(diff))} vs last year`, tone: diff > 0 ? "up" : "down", arrow: diff > 0 ? "▲" : "▼" };
        };
        const w = this.windowLabel;
        return [
            { key: "inv", label: "Invoiced", value: this.fmt(inv), tone: "teal", drill: true,
              sub: p.x_is_future && !inv ? "Period not started" : "Posted invoices to date",
              open: () => this.drillTo({ kind: "invoices", title: `Invoiced · ${w} ${y}`, years: [y], months: this.windowMonths }) },
            { key: "out", label: "Outlook", value: this.fmt(all), tone: "navy", drill: true,
              sub: `Invoiced + ${this.fmt(bud)} budget to come`, delta: delta(all, before),
              open: () => this.openFigure({ title: `Outlook · ${w} ${y}`, years: [y], inv, bud }) },
            { key: "gr", label: "vs Last Year", value: growth === null ? "–" : `${growth.toFixed(1)}%`, drill: true,
              tone: growth === null || growth >= 0 ? "green" : "red", sub: `Same period last year ${this.fmt(before)}`,
              open: () => this.openCells(`${w}: ${y - 1} against ${y}`, null, [y - 1, y], ["x_year"]) },
            { key: "cu", label: "Customers", value: String(g.active.length), tone: "purple", drill: true,
              sub: `${g.fresh.length} new · ${g.lapsed.length} lapsed`,
              open: () => this.openCustomers(`Customers buying · ${w} ${y}`, g.active) },
            { key: "nw", label: "From New Customers", value: this.fmt(newRevenue), tone: "amber", drill: true,
              sub: "No sales in the same period last year",
              open: () => this.openCells(`New customers · ${w} ${y}`, g.fresh.length ? g.fresh : [{ id: 0 }], [y]) },
            { key: "t5", label: "Top 5 Share", value: all ? `${Math.round((top5 / all) * 100)}%` : "–", drill: true,
              tone: "red", sub: `${this.fmt(top5)} from the five largest`,
              open: () => this.openCells(`Top 5 customers · ${w} ${y}`, g.top5.length ? g.top5 : [{ id: 0 }], [y], ["x_customer_id"]) },
        ];
    }

    // ------------------------------------------------------------ formatting
    fmt(value, compact = false) {
        const v = value || 0;
        try {
            return new Intl.NumberFormat("en-US", {
                style: "currency", currency: this.currency, maximumFractionDigits: 0,
                notation: compact ? "compact" : "standard",
            }).format(v);
        } catch {
            return Math.round(v).toLocaleString();
        }
    }

    // ------------------------------------------------------------ charts
    renderChartsIfNeeded() {
        const d = this.state.dashboard;
        const key = [this.state.loading, this.state.dashboardId, this.state.selectedCode,
            d && d.x_refreshed, this.state.customers.length].join("|");
        if (key !== this.chartKey || !Object.keys(this.charts).length) {
            this.chartKey = key;
            this.renderCharts();
        }
    }

    destroyCharts() {
        for (const chart of Object.values(this.charts)) {
            chart.destroy();
        }
        this.charts = {};
    }

    baseOptions(extra = {}) {
        return Object.assign({
            responsive: true, maintainAspectRatio: false, animation: { duration: 250 },
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 10, usePointStyle: true, color: C.slate, font: { size: 11 } } },
                tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${this.fmt(ctx.parsed.y !== undefined ? ctx.parsed.y : ctx.parsed.x)}` } },
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: C.slate, font: { size: 11 } } },
                y: { grid: { color: C.grid }, ticks: { color: C.slate, font: { size: 11 }, callback: (v) => this.fmt(v, true) } },
            },
        }, extra);
    }

    make(key, config) {
        const el = this.refs[key] && this.refs[key].el;
        if (!el || !window.Chart) {
            return;
        }
        if (this.charts[key]) {
            this.charts[key].destroy();
        }
        this.charts[key] = new window.Chart(el, config);
    }

    renderCharts() {
        if (this.state.loading || !this.hasData) {
            this.destroyCharts();
            return;
        }
        const years = this.years;
        const rows = this.rows;
        const d = this.state.dashboard;

        const inv = years.map((y) => rows.reduce((a, r) => a + this.value(r.customer.id, y, "inv"), 0));
        const bud = years.map((y) => rows.reduce((a, r) => a + this.value(r.customer.id, y, "bud"), 0));
        this.make("years", {
            type: "bar",
            data: { labels: years.map(String), datasets: [
                { label: "Invoiced", data: inv, backgroundColor: C.teal, borderRadius: 6, maxBarThickness: 46, stack: "s" },
                { label: "Budget to come", data: bud, backgroundColor: C.amber, borderRadius: 6, maxBarThickness: 46, stack: "s" },
            ] },
            options: this.baseOptions(Object.assign(this.clickable((i, ds) => this.openYear(years[i], ds === 1 ? "bud" : "inv")), {
                scales: {
                    x: { stacked: true, grid: { display: false }, ticks: { color: C.slate } },
                    y: { stacked: true, grid: { color: C.grid }, ticks: { color: C.slate, callback: (v) => this.fmt(v, true) } },
                },
            })),
        });

        const monthInv = [], monthBud = [], monthPrev = [];
        for (let m = 1; m <= 12; m++) {
            let i = 0, b = 0, p = 0;
            for (const r of rows) {
                const byYear = this.index[r.customer.id] || {};
                const now = (byYear[d.x_year] || {})[m];
                const before = (byYear[d.x_year - 1] || {})[m];
                if (now) { i += now.inv; b += now.bud; }
                if (before) { p += before.inv + before.bud; }
            }
            monthInv.push(i); monthBud.push(b || null); monthPrev.push(p);
        }
        this.make("months", {
            type: "bar",
            data: { labels: MONTHS, datasets: [
                { label: `Invoiced ${d.x_year}`, data: monthInv, backgroundColor: C.teal, borderRadius: 4, maxBarThickness: 22 },
                { label: "Budget to come", data: monthBud, backgroundColor: C.amber, borderRadius: 4, maxBarThickness: 22 },
                { type: "line", label: String(d.x_year - 1), data: monthPrev, borderColor: C.navy, backgroundColor: C.navy, tension: 0.3, pointRadius: 3 },
            ] },
            options: this.baseOptions(this.clickable((i, ds) => {
                const month = i + 1;
                const name = MONTHS[i];
                if (ds === 0) {
                    return this.drillTo({ kind: "invoices", title: `Invoiced · ${name} ${d.x_year}`, years: [d.x_year], months: [month] });
                }
                if (ds === 1) {
                    return this.drillTo({ kind: "budget", title: `Budget to come · ${name} ${d.x_year}`, years: [d.x_year], months: [month] });
                }
                const all = this.state.customers;
                return this.openFigure({ title: `${name} ${d.x_year - 1}`, years: [d.x_year - 1], months: [month],
                    inv: this.sumFor(all, d.x_year - 1, "inv", [month]), bud: this.sumFor(all, d.x_year - 1, "bud", [month]) });
            })),
        });

        const top = rows.slice(0, 15);
        this.make("top", {
            type: "bar",
            data: { labels: top.map((r) => r.customer.x_name), datasets: [
                { label: String(d.x_year), data: top.map((r) => r.total), backgroundColor: C.teal, borderRadius: 4, maxBarThickness: 16 },
                { label: String(d.x_year - 1), data: top.map((r) => r.prev), backgroundColor: C.light, borderRadius: 4, maxBarThickness: 16 },
            ] },
            options: this.baseOptions(Object.assign(this.clickable((i, ds) => this.openCustomer(top[i], ds === 1 ? d.x_year - 1 : d.x_year)), {
                indexAxis: "y",
                scales: {
                    x: { grid: { color: C.grid }, ticks: { color: C.slate, callback: (v) => this.fmt(v, true) } },
                    y: { grid: { display: false }, ticks: { color: C.slate, font: { size: 11 } } },
                },
            })),
        });

        // the same four groups the KPI cards and the drill-down use, so the bars add up exactly
        const g = this.groups;
        const byId = {};
        for (const r of rows) {
            byId[r.customer.id] = r;
        }
        const sumOf = (list, fn) => list.reduce((acc, c) => acc + fn(byId[c.id]), 0);
        const start = rows.reduce((acc, r) => acc + r.prev, 0);
        const won = sumOf(g.fresh, (r) => r.total);
        const grew = sumOf(g.grew, (r) => r.total - r.prev);
        const shrank = sumOf(g.shrank, (r) => r.total - r.prev);
        const lost = sumOf(g.lapsed, (r) => -r.prev);
        const steps = [
            [String(d.x_year - 1), start, "base"], ["New customers", won, "up"], ["Grew", grew, "up"],
            ["Shrank", shrank, "down"], ["Lapsed", lost, "down"], [String(d.x_year), start + won + grew + shrank + lost, "base"],
        ];
        let running = 0;
        const bars = steps.map(([, v, kind]) => {
            if (kind === "base") { running = v; return [0, v]; }
            const from = running; running += v; return [from, running];
        });
        this.make("bridge", {
            type: "bar",
            data: { labels: steps.map((s) => s[0]), datasets: [{ label: "Change", data: bars,
                backgroundColor: steps.map((s) => (s[2] === "base" ? C.navy : s[2] === "up" ? C.teal : C.amber)),
                borderRadius: 5, maxBarThickness: 48 }] },
            options: this.baseOptions(Object.assign(this.clickable((i) => {
                const g = this.groups;
                const w = this.windowLabel;
                const sets = [null, g.fresh, g.grew, g.shrank, g.lapsed, null];
                if (i === 0) {
                    return this.openYear(d.x_year - 1);
                }
                if (i === steps.length - 1) {
                    return this.openYear(d.x_year);
                }
                const list = sets[i] && sets[i].length ? sets[i] : [{ id: 0 }];
                return this.openCells(`${steps[i][0]} · ${w}: ${d.x_year - 1} to ${d.x_year}`, list,
                    [d.x_year - 1, d.x_year], ["x_customer_id"]);
            }), { plugins: { legend: { display: false },
                tooltip: { callbacks: { label: (ctx) => this.fmt(steps[ctx.dataIndex][1]) } } } })),
        });

        const all = rows.reduce((a, r) => a + Math.max(r.total, 0), 0);
        const five = rows.slice(0, 5).reduce((a, r) => a + Math.max(r.total, 0), 0);
        this.make("mix", {
            type: "doughnut",
            data: { labels: ["Top 5 customers", "Everyone else"],
                datasets: [{ data: [five, Math.max(all - five, 0)], backgroundColor: [C.teal, C.light], borderWidth: 0 }] },
            options: { responsive: true, maintainAspectRatio: false, cutout: "68%",
                ...this.clickable((i) => {
                    const g = this.groups;
                    const list = i === 0 ? g.top5 : g.others;
                    return this.openCells(`${i === 0 ? "Top 5 customers" : "Everyone else"} · ${this.windowLabel} ${d.x_year}`,
                        list.length ? list : [{ id: 0 }], [d.x_year], ["x_customer_id"]);
                }),
                interaction: { mode: "nearest", intersect: true },
                plugins: { legend: { position: "bottom", labels: { boxWidth: 10, usePointStyle: true, color: C.slate } },
                    tooltip: { callbacks: { label: (ctx) => `${ctx.label}: ${this.fmt(ctx.parsed)}` } } } },
        });
    }
}

registry.category("actions").add("x_invcmp_dashboard", InvoiceComparisonDashboard);
