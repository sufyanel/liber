/** @odoo-module **/
/* Income Statement Dashboard - Axiom World
 * Built like the Threshold Dashboard: one dashboard per company and year,
 * Q1-Q4 / FY / custom range tabs, KPI cards, charts and a drill-down table.
 * Every line, label, sign and formula comes from the dashboard's own lines. */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { useSetupAction } from "@web/webclient/actions/action_hook";
import { Component, useState, useRef, onWillStart, onMounted, onPatched, onWillUnmount } from "@odoo/owl";

const C = {
    navy: "#13294B", teal: "#0E7C86", sky: "#5FB3BA", amber: "#E0892B", green: "#15803D",
    red: "#C2410C", purple: "#5B2A86", slate: "#64748B", grid: "rgba(100,116,139,0.15)", light: "#CBD5E1",
};
const PALETTE = [C.teal, C.amber, C.purple, C.green, C.red, C.navy];

export class IncomeStatementDashboard extends Component {
    static template = "x_isr_dashboard.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        this.params = (this.props.action && this.props.action.params) || {};
        this.state = useState({
            loading: true, refreshing: false, applying: false, downloading: false,
            dashboards: [], dashboardId: null, dashboard: null,
            periods: [], lines: [], selectedCode: null, customFrom: "", customTo: "",
        });
        this.values = {};
        // come back from a drill-down to the same dashboard and tab
        const saved = this.props.state || {};
        this.state.dashboardId = saved.dashboardId || null;
        this.state.selectedCode = saved.selectedCode || null;
        useSetupAction({
            getLocalState: () => ({ dashboardId: this.state.dashboardId, selectedCode: this.state.selectedCode }),
        });
        this.refs = {
            waterfall: useRef("waterfall"), budget: useRef("budget"),
            trend: useRef("trend"), margins: useRef("margins"),
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
        const dashboards = await this.orm.searchRead("x_isr_dashboard", [],
            ["x_name", "x_company_id", "x_year", "x_prior_years", "x_peer_company_ids",
             "x_currency_code", "x_refreshed", "x_custom_from", "x_custom_to"],
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
        const [periods, lines, values] = await Promise.all([
            this.orm.searchRead("x_isr_period", [["x_dashboard_id", "=", id]],
                ["x_name", "x_code", "x_sequence", "x_date_from", "x_date_to", "x_is_future", "x_is_year",
                 "x_is_prior", "x_is_custom", "x_revenue", "x_budget_revenue"], { order: "x_sequence, id" }),
            this.orm.searchRead("x_isr_line", [["x_dashboard_id", "=", id]],
                ["x_name", "x_key", "x_sequence", "x_kind", "x_formula", "x_sign", "x_bold", "x_show_pct",
                 "x_is_revenue", "x_bridge", "x_kpi", "x_budget_pct", "x_resolved_account_ids"],
                { order: "x_sequence, id" }),
            this.orm.searchRead("x_isr_value", [["x_dashboard_id", "=", id]],
                ["x_period_id", "x_key", "x_amount", "x_budget", "x_pct"]),
        ]);
        this.state.periods = periods;
        this.state.lines = lines;
        const index = {};
        for (const v of values) {
            const pid = v.x_period_id[0];
            index[pid] = index[pid] || {};
            index[pid][v.x_key] = v;
        }
        this.values = index;
        const d = this.state.dashboard;
        // refresh quietly in the background when the snapshot is more than an hour old
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
            periods.find((p) => p.x_code === this.state.selectedCode && !p.x_is_future && !p.x_is_custom && !p.x_is_prior);
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

    onDateChange() {
        // recalculate automatically shortly after the last change (no Calculate / Refresh click)
        clearTimeout(this._dateTimer);
        this._dateTimer = setTimeout(() => this.applyCustomRange(true), 600);
    }

    runContext(extra) {
        return Object.assign({
            active_model: "x_isr_dashboard",
            active_id: this.state.dashboardId,
            active_ids: [this.state.dashboardId],
        }, extra || {});
    }

    async refresh() {
        if (!this.params.refresh_action_id || !this.state.dashboardId) {
            return;
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
            await this.orm.write("x_isr_dashboard", [this.state.dashboardId],
                { x_custom_from: from, x_custom_to: to });
            await this.orm.call("ir.actions.server", "run", [[this.params.refresh_action_id]],
                { context: this.runContext() });
            const keep = this.state.selectedCode;
            await this.loadDashboards();
            this.state.selectedCode = keep || "CUSTOM";
            if (!silent) {
                this.notification.add(`Calculated ${from} to ${to}`, { type: "success" });
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
                [[this.params.export_action_id]], { context: this.runContext() });
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
    // Every figure opens what it adds up: journal items for an account-based line,
    // the lines a subtotal is made of for a calculated line, and the planned revenue
    // and Budget % behind a budget. The server builds the list with the same domain
    // the refresh used, so the list always matches the figure.
    async drill(line, period, kind = "actual") {
        if (!line || !period || !this.params.refresh_action_id) {
            return;
        }
        if (kind === "actual" && period.x_is_future) {
            this.notification.add(`${period.x_name} has not started yet.`, { type: "info" });
            return;
        }
        const action = await this.orm.call("ir.actions.server", "run", [[this.params.refresh_action_id]],
            { context: this.runContext({ isr_drill: { line_id: line.id, period_id: period.id, kind } }) });
        if (action) {
            this.lastDrill = { line: line.x_key, period: period.x_code, kind };
            await this.actionService.doAction(action);
        }
    }

    onKpiClick(k) {
        this.drill(k.line, this.selected);
    }

    onCellClick(line, column) {
        this.drill(line, column.period, column.kind === "budget" ? "budget" : "actual");
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
    get standardPeriods() {
        return this.state.periods.filter((p) => !p.x_is_prior && !p.x_is_custom);
    }
    get priorPeriods() {
        return this.state.periods.filter((p) => p.x_is_prior);
    }
    get quarters() {
        return this.state.periods.filter((p) => !p.x_is_year);
    }
    get customPeriod() {
        return this.state.periods.find((p) => p.x_is_custom) || null;
    }
    get selected() {
        return this.state.periods.find((p) => p.x_code === this.state.selectedCode) || null;
    }
    get previous() {
        const p = this.selected;
        if (!p || p.x_is_custom) {
            return null;
        }
        if (p.x_code === "FY") {
            return this.state.periods.find((x) => x.x_code === `Y${this.state.dashboard.x_year - 1}`) || null;
        }
        const index = this.quarters.findIndex((q) => q.x_code === p.x_code);
        return index > 0 ? this.quarters[index - 1] : null;
    }
    get revenueLine() {
        return this.state.lines.find((l) => l.x_is_revenue) || null;
    }
    get closingLine() {
        return this.state.lines.find((l) => l.x_bridge === "total") || this.state.lines[this.state.lines.length - 1];
    }

    fig(period, key) {
        return (period && this.values[period.id] && this.values[period.id][key]) || { x_amount: 0, x_budget: 0, x_pct: 0 };
    }

    pct(value) {
        return value === null || value === undefined ? "–" : `${value.toFixed(1)}%`;
    }

    get kpis() {
        const p = this.selected;
        if (!p) {
            return [];
        }
        const q = this.previous;
        const out = [];
        for (const line of this.state.lines.filter((l) => l.x_kpi).slice(0, 6)) {
            const f = this.fig(p, line.x_key);
            let delta = null;
            if (q) {
                const diff = f.x_amount - this.fig(q, line.x_key).x_amount;
                delta = Math.abs(diff) < 0.5
                    ? { text: `no change vs ${q.x_name}`, tone: "flat", arrow: "→" }
                    : { text: `${this.fmt(Math.abs(diff))} vs ${q.x_name}`, tone: diff > 0 ? "up" : "down", arrow: diff > 0 ? "▲" : "▼" };
            }
            const sub = line.x_is_revenue
                ? (p.x_budget_revenue ? `Budget ${this.fmt(p.x_budget_revenue)}` : "No budget for this period")
                : `${this.pct(p.x_revenue ? (f.x_amount / p.x_revenue) * 100 : null)} of sales` +
                  (p.x_budget_revenue ? ` · budget ${this.fmt(f.x_budget)}` : "");
            out.push({
                key: line.x_key, line, label: line.x_name, value: p.x_is_future ? "–" : this.fmt(f.x_amount), sub, delta,
                tone: line.x_is_revenue ? "navy" : (f.x_amount >= 0 ? "teal" : "red"),
            });
        }
        return out;
    }

    get columns() {
        const cols = [];
        for (const p of this.priorPeriods) {
            cols.push({ key: p.x_code, label: p.x_name, period: p, kind: "actual", css: "" });
        }
        for (const p of this.standardPeriods) {
            cols.push({ key: p.x_code, label: p.x_name, period: p, kind: "actual", css: p.x_code === "FY" ? "fy" : "" });
        }
        if (this.customPeriod) {
            cols.push({ key: "CUSTOM", label: "Custom", period: this.customPeriod, kind: "actual", css: "custom" });
        }
        const fy = this.state.periods.find((p) => p.x_code === "FY");
        if (fy && fy.x_budget_revenue) {
            cols.push({ key: "BUDGET", label: `Budget ${this.state.dashboard.x_year}`, period: fy, kind: "budget", css: "fy" });
        }
        return cols;
    }

    get tableRows() {
        const cols = this.columns;
        return this.state.lines.map((line) => ({
            line,
            css: line.x_bold ? "strong" : "",
            cells: cols.map((col) => {
                const f = this.fig(col.period, line.x_key);
                const future = col.kind === "actual" && col.period.x_is_future;
                const amount = col.kind === "budget" ? f.x_budget : f.x_amount;
                const base = col.kind === "budget" ? col.period.x_budget_revenue : col.period.x_revenue;
                return {
                    key: col.key, css: col.css, future, negative: !future && amount < 0,
                    selected: col.key === this.state.selectedCode,
                    text: future ? "–" : this.fmt(amount),
                    sub: !future && line.x_show_pct && base ? this.pct((amount / base) * 100) : "",
                    col,
                };
            }),
        }));
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
            d && d.x_refreshed, this.state.periods.length].join("|");
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
        const p = this.selected;
        if (this.state.loading || !this.hasData || !p) {
            this.destroyCharts();
            return;
        }

        // From revenue to the bottom line
        const steps = [];
        let running = 0;
        for (const line of this.state.lines.filter((l) => l.x_bridge && l.x_bridge !== "none")) {
            const v = this.fig(p, line.x_key).x_amount;
            if (line.x_bridge === "base" || line.x_bridge === "total") {
                running = v;
                steps.push({ line, range: [0, v], value: v, color: line.x_bridge === "base" ? C.navy : C.green });
            } else {
                steps.push({ line, range: [running, running + v], value: v, color: v >= 0 ? C.teal : C.amber });
                running += v;
            }
        }
        this.make("waterfall", {
            type: "bar",
            data: { labels: steps.map((s) => s.line.x_name), datasets: [{ label: "Amount", data: steps.map((s) => s.range),
                backgroundColor: steps.map((s) => s.color), borderRadius: 5, maxBarThickness: 46 }] },
            options: this.baseOptions(Object.assign(this.clickable((i) => this.drill(steps[i].line, p)), {
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => this.fmt(steps[ctx.dataIndex].value) } } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: C.slate, font: { size: 10 }, maxRotation: 45, minRotation: 30 } },
                    y: { grid: { color: C.grid }, ticks: { color: C.slate, callback: (v) => this.fmt(v, true) } },
                },
            })),
        });

        // Actual against budget for the KPI lines
        const kpiLines = this.state.lines.filter((l) => l.x_kpi);
        this.make("budget", {
            type: "bar",
            data: { labels: kpiLines.map((l) => l.x_name), datasets: [
                { label: "Actual", data: kpiLines.map((l) => this.fig(p, l.x_key).x_amount), backgroundColor: C.teal, borderRadius: 4, maxBarThickness: 16 },
                { label: "Budget", data: kpiLines.map((l) => this.fig(p, l.x_key).x_budget), backgroundColor: C.amber, borderRadius: 4, maxBarThickness: 16 },
            ] },
            options: this.baseOptions(Object.assign(this.clickable((i, ds) => this.drill(kpiLines[i], p, ds === 1 ? "budget" : "actual")), {
                indexAxis: "y",
                scales: {
                    x: { grid: { color: C.grid }, ticks: { color: C.slate, callback: (v) => this.fmt(v, true) } },
                    y: { grid: { display: false }, ticks: { color: C.slate, font: { size: 11 } } },
                },
            })),
        });

        // The quarters of the year
        const quarters = this.quarters;
        const rev = this.revenueLine;
        const closing = this.closingLine;
        this.make("trend", {
            type: "bar",
            data: { labels: quarters.map((q) => q.x_code), datasets: [
                { label: rev ? rev.x_name : "Revenue", data: quarters.map((q) => (q.x_is_future ? null : q.x_revenue)), backgroundColor: C.teal, borderRadius: 6, maxBarThickness: 40 },
                { label: "Planned revenue", data: quarters.map((q) => q.x_budget_revenue || null), backgroundColor: C.light, borderRadius: 6, maxBarThickness: 40 },
                { type: "line", label: closing ? closing.x_name : "Result", data: quarters.map((q) => (q.x_is_future ? null : this.fig(q, closing.x_key).x_amount)),
                  borderColor: C.navy, backgroundColor: C.navy, tension: 0.3, pointRadius: 3 },
            ] },
            options: this.baseOptions(this.clickable((i, ds) => {
                const q = quarters[i];
                if (ds === 1) {
                    return this.drill(rev, q, "budget");
                }
                return this.drill(ds === 2 ? closing : rev, q);
            })),
        });

        // Each margin as a share of sales, year by year
        const years = [...this.priorPeriods, ...this.state.periods.filter((x) => x.x_code === "FY")];
        const marginLines = this.state.lines.filter((l) => l.x_kpi && !l.x_is_revenue);
        this.make("margins", {
            type: "line",
            data: { labels: years.map((y) => y.x_name), datasets: marginLines.map((l, i) => ({
                label: l.x_name, data: years.map((y) => (y.x_revenue ? (this.fig(y, l.x_key).x_amount / y.x_revenue) * 100 : null)),
                borderColor: PALETTE[i % PALETTE.length], backgroundColor: PALETTE[i % PALETTE.length], tension: 0.25, pointRadius: 3,
            })) },
            options: this.baseOptions({
                ...this.clickable((i, ds) => this.drill(marginLines[ds], years[i])),
                plugins: {
                    legend: { position: "bottom", labels: { boxWidth: 10, usePointStyle: true, color: C.slate, font: { size: 11 } } },
                    tooltip: { callbacks: { label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y === null ? "–" : ctx.parsed.y.toFixed(1) + "%"}` } },
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: C.slate } },
                    y: { grid: { color: C.grid }, ticks: { color: C.slate, callback: (v) => `${v}%` } },
                },
            }),
        });
    }
}

registry.category("actions").add("x_isr_dashboard", IncomeStatementDashboard);
