/** @odoo-module **/
/* Threshold Report Dashboard - Axiom World
 * OWL client action (tag: x_threshold_dashboard). Reads the period and vendor
 * records produced by the "Refresh Threshold Dashboard" server action and
 * renders KPI cards and Chart.js visuals. */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { loadBundle } from "@web/core/assets";
import { Component, useState, useRef, onWillStart, onMounted, onPatched, onWillUnmount } from "@odoo/owl";

const C = {
    navy: "#13294B", teal: "#0E7C86", tealSoft: "rgba(14,124,134,0.18)", sky: "#5FB3BA",
    amber: "#E0892B", amberSoft: "rgba(224,137,43,0.18)", red: "#C2410C", green: "#15803D",
    slate: "#64748B", grid: "rgba(100,116,139,0.15)", purple: "#5B2A86", light: "#CBD5E1",
};

const PL_TYPES = ["income", "income_other", "expense", "expense_depreciation", "expense_direct_cost"];
// Threshold line -> Threshold Report account mapping row
const FIELD_ROW = {
    x_salary: "salary", x_taxes: "taxes", x_depreciation: "depreciation", x_capex: "capital_investments",
    x_change_ar: "change_ar", x_change_inventory: "change_inventory", x_debt: "debt_retirement",
    x_investor: "investor_return", x_savings: "savings", x_net_change: "change_ar",
};
const LABELS = {
    x_net_profit: "Net Profit", x_salary: "Salary", x_taxes: "Taxes", x_depreciation: "Depreciation",
    x_capex: "Capital Investments", x_change_ar: "Change in A/R", x_change_ap: "Change in A/P",
    x_net_change: "Net Change in A/R and A/P", x_change_inventory: "Change in Inventory", x_debt: "Debt Retirement",
    x_investor: "Investor Return", x_savings: "Savings", x_threshold: "Financial Security Threshold",
    x_headroom: "Headroom", x_pool: "Gain-share Pool", x_payout_period: "Scheduled Payout",
};
const WATERFALL_FIELDS = [null, "x_taxes", "x_depreciation", "x_capex", "x_net_change", "x_change_inventory",
    "x_debt", "x_investor", "x_savings", null];

const PERIOD_FIELDS = [
    "x_name", "x_code", "x_sequence", "x_date_from", "x_date_to", "x_is_future", "x_is_year", "x_payout_pct",
    "x_net_profit", "x_salary", "x_taxes", "x_depreciation", "x_capex", "x_change_ar", "x_change_ap", "x_net_change",
    "x_change_inventory", "x_debt", "x_investor", "x_savings", "x_threshold", "x_headroom", "x_pool",
    "x_ytd_headroom", "x_ytd_pool", "x_payout_cum", "x_payout_period", "x_ap_opening", "x_ap_closing",
    "x_source_ap_closing", "x_is_custom",
];

export class ThresholdDashboard extends Component {
    static template = "x_threshold_dashboard.Dashboard";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.notification = useService("notification");
        const params = (this.props.action && this.props.action.params) || {};
        this.params = params;
        this.state = useState({
            loading: true, refreshing: false, dashboards: [], dashboardId: null, dashboard: null,
            periods: [], vendors: [], selectedCode: null, customFrom: "", customTo: "", applying: false,
        });
        this.mappings = {};
        this.apRuleId = null;
        this.refs = {
            waterfall: useRef("waterfall"), gauge: useRef("gauge"), trend: useRef("trend"),
            ytd: useRef("ytd"), arap: useRef("arap"), donut: useRef("donut"), vendors: useRef("vendors"),
        };
        this.charts = {};
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await this.loadDashboards();
        });
        this.chartKey = null;
        onMounted(() => this.renderChartsIfNeeded());
        onPatched(() => this.renderChartsIfNeeded());
        onWillUnmount(() => this.destroyCharts());
    }

    // ------------------------------------------------------------ data
    async loadDashboards() {
        const dashboards = await this.orm.searchRead(
            "x_threshold_dashboard", [],
            ["x_name", "x_company_id", "x_year", "x_currency_code", "x_refreshed", "x_employee_share",
             "x_payout_schedule", "x_vendor_as_of", "x_has_ap_rule", "x_custom_from", "x_custom_to"],
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
        const [periods, vendors] = await Promise.all([
            this.orm.searchRead("x_threshold_dashboard_period", [["x_dashboard_id", "=", id]], PERIOD_FIELDS,
                { order: "x_sequence, id" }),
            this.orm.searchRead("x_threshold_dashboard_vendor", [["x_dashboard_id", "=", id]],
                ["x_name", "x_amount", "x_documents"], { order: "x_amount desc, id" }),
        ]);
        this.state.periods = periods;
        this.state.vendors = vendors;
        const d = this.state.dashboard;
        this.state.customFrom = d.x_custom_from || `${d.x_year}-01-01`;
        this.state.customTo = d.x_custom_to || new Date().toISOString().slice(0, 10);
        await this.loadDrillData(d.x_company_id[0]);
        const quarters = periods.filter((p) => !p.x_is_year && !p.x_is_future);
        if (this.state.selectedCode === "CUSTOM" && periods.some((p) => p.x_is_custom)) {
            this.state.loading = false;
            return;
        }
        const current = this.state.selectedCode && periods.find((p) => p.x_code === this.state.selectedCode && !p.x_is_future);
        this.state.selectedCode = current ? current.x_code : (quarters.length ? quarters[quarters.length - 1].x_code : "FY");
        this.state.loading = false;
    }

    async onDashboardChange(ev) {
        await this.selectDashboard(parseInt(ev.target.value));
    }

    selectPeriod(code) {
        this.state.selectedCode = code;
    }

    async refresh() {
        if (!this.params.refresh_action_id || !this.state.dashboardId) {
            return;
        }
        this.state.refreshing = true;
        try {
            await this.orm.call("ir.actions.server", "run", [[this.params.refresh_action_id]], {
                context: {
                    active_model: "x_threshold_dashboard",
                    active_id: this.state.dashboardId,
                    active_ids: [this.state.dashboardId],
                },
            });
            await this.loadDashboards();
            this.notification.add("Dashboard refreshed", { type: "success" });
        } finally {
            this.state.refreshing = false;
        }
    }

    openSettings() {
        if (this.params.settings_action_id) {
            this.actionService.doAction(this.params.settings_action_id);
        }
    }

    openReport() {
        const p = this.selected;
        const ctx = { default_company_id: this.state.dashboard.x_company_id[0], default_year: String(this.state.dashboard.x_year) };
        if (p && p.x_is_custom) {
            this.notification.add("The printed Threshold Report supports a year, quarter or month; opening it for the year.", { type: "info" });
            ctx.default_duration = "year";
        } else if (p && !p.x_is_year) {
            Object.assign(ctx, { default_duration: "quarter", default_quarter: p.x_code });
        } else {
            ctx.default_duration = "year";
        }
        this.actionService.doAction(this.params.report_action_id, { additionalContext: ctx });
    }

    openApBreakdown() {
        if (this.params.ap_action_id) {
            this.actionService.doAction(this.params.ap_action_id);
        }
    }


    // ------------------------------------------------------------ custom range
    async applyCustomRange() {
        const from = this.state.customFrom;
        const to = this.state.customTo;
        if (!from || !to || from > to) {
            this.notification.add("Choose a start date on or before the end date.", { type: "warning" });
            return;
        }
        this.state.applying = true;
        try {
            await this.orm.write("x_threshold_dashboard", [this.state.dashboardId], { x_custom_from: from, x_custom_to: to });
            await this.orm.call("ir.actions.server", "run", [[this.params.refresh_action_id]], {
                context: {
                    active_model: "x_threshold_dashboard", active_id: this.state.dashboardId,
                    active_ids: [this.state.dashboardId], threshold_custom_only: true,
                },
            });
            this.state.selectedCode = "CUSTOM";
            await this.loadDashboards();
            this.notification.add(`Calculated ${from} to ${to}`, { type: "success" });
        } finally {
            this.state.applying = false;
        }
    }

    // ------------------------------------------------------------ drill-down
    async loadDrillData(companyId) {
        this.mappings = {};
        this.apRuleId = null;
        try {
            const maps = await this.orm.searchRead("threshold.report.account.mapping", [["company_id", "=", companyId]],
                ["row_key", "line_ids", "amount"]);
            const lineIds = maps.flatMap((m) => m.line_ids);
            const lines = lineIds.length ? await this.orm.read("threshold.report.account.mapping.line", lineIds, ["account_id"]) : [];
            const accountOf = {};
            for (const l of lines) {
                accountOf[l.id] = l.account_id && l.account_id[0];
            }
            for (const m of maps) {
                this.mappings[m.row_key] = { accounts: m.line_ids.map((i) => accountOf[i]).filter(Boolean), amount: m.amount };
            }
            const rules = await this.orm.searchRead("x_threshold_ap_rule", [["x_company_id", "=", companyId]], ["id"], { limit: 1 });
            this.apRuleId = rules.length ? rules[0].id : null;
        } catch {
            // Drill-down is optional; the dashboard still works without it.
        }
    }

    periodByCode(code) {
        return this.state.periods.find((p) => p.x_code === code);
    }

    async drill(field, period) {
        if (!field || !period || period.x_is_future) {
            return;
        }
        const label = LABELS[field] || "Detail";
        const range = [["date", ">=", period.x_date_from], ["date", "<=", period.x_date_to], ["parent_state", "=", "posted"]];
        if (field === "x_net_profit") {
            return this.openLines(`${label} · ${period.x_name}`, [
                ["company_id", "=", this.state.dashboard.x_company_id[0]], ["account_id.account_type", "in", PL_TYPES], ...range]);
        }
        if (field === "x_change_ap") {
            return this.openApPreview(period);
        }
        if (FIELD_ROW[field]) {
            const mapping = this.mappings[FIELD_ROW[field]];
            if (mapping && mapping.accounts.length) {
                const name = field === "x_net_change" ? `Change in A/R · ${period.x_name}` : `${label} · ${period.x_name}`;
                if (field === "x_net_change") {
                    this.notification.add("Showing the receivables part. Click Change in A/P for the payables part.", { type: "info" });
                }
                return this.openLines(name, [["account_id", "in", mapping.accounts], ...range]);
            }
            this.notification.add(`${label} has no account mapping, so it uses the manual amount in the dashboard settings.`, { type: "info" });
            return this.openSettingsRecord();
        }
        return this.openPeriod(period);
    }

    openLines(name, domain) {
        this.actionService.doAction({
            type: "ir.actions.act_window", name, res_model: "account.move.line",
            views: [[false, "list"], [false, "form"]], domain, target: "current",
            context: { create: false },
        });
    }

    openPeriod(period) {
        this.actionService.doAction({
            type: "ir.actions.act_window", name: period.x_name, res_model: "x_threshold_dashboard_period",
            res_id: period.id, views: [[false, "form"]], target: "new",
        });
    }

    openSettingsRecord() {
        this.actionService.doAction({
            type: "ir.actions.act_window", name: "Dashboard Settings", res_model: "x_threshold_dashboard",
            res_id: this.state.dashboardId, views: [[false, "form"]], target: "current",
        });
    }

    async openApPreview(period) {
        if (!this.apRuleId || !this.params.ap_compute_action_id) {
            this.notification.add("This company has no AP allocation rule.", { type: "warning" });
            return;
        }
        const [id] = await this.orm.create("x_threshold_ap_preview", [{
            x_name: `${this.state.dashboard.x_company_id[1]} · ${period.x_name}`,
            x_rule_id: this.apRuleId, x_date_from: period.x_date_from, x_date_to: period.x_date_to,
            x_source: "Dashboard drill-down",
        }]);
        await this.orm.call("ir.actions.server", "run", [[this.params.ap_compute_action_id]], {
            context: { active_model: "x_threshold_ap_preview", active_id: id, active_ids: [id] },
        });
        this.actionService.doAction({
            type: "ir.actions.act_window", name: "AP Allocation", res_model: "x_threshold_ap_preview",
            res_id: id, views: [[false, "form"]], target: "current",
        });
    }

    openVendor(name) {
        this.actionService.doAction({
            type: "ir.actions.act_window", name: `Open bills · ${name}`, res_model: "account.move",
            views: [[false, "list"], [false, "form"]], target: "current",
            domain: [["move_type", "in", ["in_invoice", "in_refund"]], ["state", "=", "posted"],
                ["payment_state", "in", ["not_paid", "partial", "in_payment"]], ["partner_id.name", "=", name]],
            context: { create: false },
        });
    }

    onKpiClick(k) {
        this.drill(k.field, this.selected);
    }

    onCellClick(field, code) {
        const period = this.periodByCode(code);
        if (period && !period.x_is_future) {
            this.drill(field, period);
        }
    }

    clickable(handler) {
        return {
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
    get quarters() {
        return this.state.periods.filter((p) => !p.x_is_year);
    }
    get selected() {
        return this.state.periods.find((p) => p.x_code === this.state.selectedCode) || null;
    }
    get previous() {
        const p = this.selected;
        if (!p || p.x_is_year || p.x_is_custom) {
            return null;
        }
        return this.state.periods.find((x) => x.x_sequence === p.x_sequence - 1) || null;
    }
    get currency() {
        return (this.state.dashboard && this.state.dashboard.x_currency_code) || "USD";
    }
    get customPeriod() {
        return this.state.periods.find((p) => p.x_is_custom) || null;
    }
    get standardPeriods() {
        return this.state.periods.filter((p) => !p.x_is_custom);
    }
    get hasData() {
        return this.state.periods.some((p) => !p.x_is_future);
    }
    get refreshedLabel() {
        const d = this.state.dashboard && this.state.dashboard.x_refreshed;
        return d ? d.replace("T", " ").slice(0, 16) + " UTC" : "never";
    }
    get kpis() {
        const p = this.selected;
        const q = this.previous;
        if (!p) {
            return [];
        }
        const share = this.state.dashboard.x_employee_share || 0;
        const coverage = p.x_threshold < 0 ? p.x_net_profit / -p.x_threshold : null;
        const fieldOf = { np: "x_net_profit", thr: "x_threshold", head: "x_headroom", pool: "x_pool", ap: "x_change_ap", net: "x_net_change" };
        const card = (key, label, value, sub, tone, prevValue, invert = false) => ({
            key, label, value: this.fmt(value), sub, tone, field: fieldOf[key],
            delta: q && prevValue !== undefined ? this.delta(value, prevValue, invert) : null,
        });
        return [
            card("np", "Net Profit", p.x_net_profit, "P&L accounts for the period", "navy", q && q.x_net_profit),
            card("thr", "Financial Security Threshold", p.x_threshold, "Cash requirements (report formula)",
                p.x_threshold < 0 ? "amber" : "teal", q && q.x_threshold),
            card("head", "Headroom above Threshold", p.x_headroom,
                coverage !== null ? `Profit covers ${Math.round(coverage * 100)}% of requirements` : "No cash requirement",
                p.x_headroom >= 0 ? "green" : "red", q && q.x_headroom),
            card("pool", "Gain-share Pool", p.x_pool, `${share}% of positive headroom (estimate)`, "purple", q && q.x_pool),
            card("ap", "Change in A/P", p.x_change_ap, this.state.dashboard.x_has_ap_rule ? "Allocated from purchasing company" : "From account mapping",
                "teal", q && q.x_change_ap),
            card("net", "Net Change A/R & A/P", p.x_net_change, `A/R ${this.fmt(p.x_change_ar)} · A/P ${this.fmt(p.x_change_ap)}`,
                "navy", q && q.x_net_change),
        ];
    }
    get tableRows() {
        const rows = [
            ["Net Profit", "x_net_profit", 1, "strong"],
            ["Taxes", "x_taxes", -1, ""],
            ["Add back Depreciation", "x_depreciation", 1, ""],
            ["Capital Investments", "x_capex", -1, ""],
            ["Change in A/R", "x_change_ar", 0, "muted"],
            ["Change in A/P (allocated)", "x_change_ap", 0, "muted"],
            ["Net Change in A/R and A/P", "x_net_change", 1, ""],
            ["Change in Inventory", "x_change_inventory", 1, ""],
            ["Debt Retirement - Principal", "x_debt", -1, ""],
            ["Investor Return", "x_investor", -1, ""],
            ["Savings", "x_savings", -1, ""],
            ["Financial Security Threshold", "x_threshold", 1, "total"],
            ["Headroom above Threshold", "x_headroom", 1, "total"],
            ["Gain-share Pool", "x_pool", 1, "strong"],
            ["Scheduled Payout (period)", "x_payout_period", 1, ""],
        ];
        return rows.map(([label, field, sign, css]) => ({
            label, css, field,
            cells: this.state.periods.map((p) => ({
                key: p.x_code, future: p.x_is_future, year: p.x_is_year && !p.x_is_custom, custom: p.x_is_custom,
                text: p.x_is_future ? "–" : this.fmt(sign === -1 ? -p[field] : p[field]),
                negative: !p.x_is_future && (sign === -1 ? -p[field] : p[field]) < 0,
            })),
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
    delta(value, prev, invert) {
        const diff = (value || 0) - (prev || 0);
        if (Math.abs(diff) < 0.5) {
            return { text: "no change vs previous", tone: "flat", arrow: "→" };
        }
        const good = invert ? diff < 0 : diff > 0;
        return { text: `${this.fmt(Math.abs(diff))} vs previous`, tone: good ? "up" : "down", arrow: diff > 0 ? "▲" : "▼" };
    }

    // ------------------------------------------------------------ charts
    renderChartsIfNeeded() {
        const d = this.state.dashboard;
        const key = [this.state.loading, this.state.dashboardId, this.state.selectedCode,
            d && d.x_refreshed, this.state.periods.length, this.state.vendors.length].join("|");
        if (key !== this.chartKey || !Object.keys(this.charts).length) {
            this.chartKey = key;
            this.renderCharts();
        }
    }

    destroyCharts() {
        for (const key of Object.keys(this.charts)) {
            this.charts[key].destroy();
        }
        this.charts = {};
    }

    baseOptions(extra = {}) {
        const self = this;
        return Object.assign({
            responsive: true, maintainAspectRatio: false, animation: { duration: 450 },
            plugins: {
                legend: { position: "bottom", labels: { boxWidth: 12, boxHeight: 12, usePointStyle: true, color: C.slate, font: { size: 12 } } },
                tooltip: {
                    backgroundColor: C.navy, padding: 10, cornerRadius: 6,
                    callbacks: {
                        label(ctx) {
                            const raw = ctx.raw;
                            const v = Array.isArray(raw) ? raw[1] - raw[0] : (typeof raw === "object" && raw !== null ? raw.y : raw);
                            return ` ${ctx.dataset.label || ctx.label}: ${self.fmt(v)}`;
                        },
                    },
                },
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: C.slate } },
                y: { grid: { color: C.grid }, border: { display: false }, ticks: { color: C.slate, callback: (v) => self.fmt(v, true) } },
            },
        }, extra);
    }

    make(key, config) {
        const ref = this.refs[key];
        if (!ref || !ref.el) {
            return;
        }
        this.charts[key] = new window.Chart(ref.el, config);
    }

    renderCharts() {
        this.destroyCharts();
        if (this.state.loading || !this.hasData || !window.Chart) {
            return;
        }
        const p = this.selected;
        const quarters = this.quarters;
        const labels = quarters.map((q) => q.x_code);
        const fade = (color, q) => (q.x_is_future ? C.light : color);

        // 1. Waterfall: Net Profit -> contributions -> Headroom
        if (p && !p.x_is_future) {
            const steps = [
                ["Taxes", -p.x_taxes], ["Depreciation", p.x_depreciation], ["Capital Inv.", -p.x_capex],
                ["Net A/R & A/P", p.x_net_change], ["Inventory", p.x_change_inventory], ["Debt", -p.x_debt],
                ["Investor", -p.x_investor], ["Savings", -p.x_savings],
            ];
            const wlabels = ["Net Profit"];
            const data = [[0, p.x_net_profit]];
            const colors = [C.navy];
            let running = p.x_net_profit;
            for (const [label, v] of steps) {
                wlabels.push(label);
                data.push([running, running + v]);
                colors.push(v >= 0 ? C.teal : C.amber);
                running += v;
            }
            wlabels.push("Headroom");
            data.push([0, running]);
            colors.push(running >= 0 ? C.green : C.red);
            this.make("waterfall", {
                type: "bar",
                data: { labels: wlabels, datasets: [{ label: "Amount", data, backgroundColor: colors, borderRadius: 4, borderSkipped: false, maxBarThickness: 46 }] },
                options: this.baseOptions({
                    plugins: Object.assign(this.baseOptions().plugins, { legend: { display: false } }),
                    ...this.clickable((i) => this.drill(i === 0 ? "x_net_profit" : (WATERFALL_FIELDS[i] || "x_headroom"), p)),
                }),
            });

            // 2. Gauge: profit coverage of cash requirements
            const need = Math.max(-p.x_threshold, 0);
            const covered = Math.min(Math.max(p.x_net_profit, 0), need || Math.max(p.x_net_profit, 0));
            const rest = need ? Math.max(need - covered, 0) : 0;
            const over = Math.max(p.x_net_profit - need, 0);
            this.make("gauge", {
                type: "doughnut",
                data: {
                    labels: ["Requirement covered", "Requirement not covered", "Headroom"],
                    datasets: [{ data: [covered, rest, over], backgroundColor: [C.teal, "#E2E8F0", C.green], borderWidth: 0 }],
                },
                options: {
                    responsive: true, maintainAspectRatio: false, rotation: -90, circumference: 180, cutout: "72%",
                    plugins: { legend: { position: "bottom", labels: { boxWidth: 10, usePointStyle: true, color: C.slate } },
                        tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${this.fmt(ctx.raw)}` } } },
                    ...this.clickable(() => this.openPeriod(p)),
                },
            });

            // 6. Donut: allocated AP vs rest of purchasing company AP at period end
            if (this.state.dashboard.x_has_ap_rule && p.x_source_ap_closing) {
                const other = Math.max(p.x_source_ap_closing - p.x_ap_closing, 0);
                this.make("donut", {
                    type: "doughnut",
                    data: { labels: ["This company", "Other companies"], datasets: [{ data: [p.x_ap_closing, other], backgroundColor: [C.teal, C.light], borderWidth: 0 }] },
                    options: { responsive: true, maintainAspectRatio: false, cutout: "68%",
                        plugins: { legend: { position: "bottom", labels: { boxWidth: 10, usePointStyle: true, color: C.slate } },
                            tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${this.fmt(ctx.raw)}` } } },
                        ...this.clickable(() => this.openApPreview(p)) },
                });
            }
        }

        // 3. Quarterly trend
        this.make("trend", {
            type: "bar",
            data: {
                labels,
                datasets: [
                    { type: "line", label: "Headroom", data: quarters.map((q) => (q.x_is_future ? null : q.x_headroom)), borderColor: C.amber,
                        backgroundColor: C.amber, tension: 0.35, pointRadius: 5, pointHoverRadius: 7, order: 0 },
                    { label: "Net Profit", data: quarters.map((q) => q.x_net_profit), backgroundColor: quarters.map((q) => fade(C.teal, q)), borderRadius: 5, order: 1, maxBarThickness: 40 },
                    { label: "Cash Requirement", data: quarters.map((q) => -q.x_threshold), backgroundColor: quarters.map((q) => fade(C.navy, q)), borderRadius: 5, order: 1, maxBarThickness: 40 },
                ],
            },
            options: this.baseOptions(this.clickable((i, ds) => {
                const q = quarters[i];
                this.drill(ds === 1 ? "x_net_profit" : (ds === 2 ? "x_threshold" : "x_headroom"), q);
            })),
        });

        // 4. YTD gain share vs payout schedule
        this.make("ytd", {
            type: "bar",
            data: {
                labels,
                datasets: [
                    { type: "line", label: "YTD Gain-share Pool", data: quarters.map((q) => (q.x_is_future ? null : q.x_ytd_pool)), borderColor: C.purple,
                        backgroundColor: "rgba(91,42,134,0.12)", fill: true, tension: 0.3, pointRadius: 5, order: 0 },
                    { label: "Cumulative Scheduled Payout", data: quarters.map((q) => (q.x_is_future ? null : q.x_payout_cum)), backgroundColor: C.sky, borderRadius: 5, order: 1, maxBarThickness: 40 },
                ],
            },
            options: this.baseOptions(this.clickable((i) => this.openPeriod(quarters[i]))),
        });

        // 5. A/R vs A/P
        this.make("arap", {
            type: "bar",
            data: {
                labels,
                datasets: [
                    { type: "line", label: "Net Change", data: quarters.map((q) => (q.x_is_future ? null : q.x_net_change)), borderColor: C.navy, backgroundColor: C.navy, tension: 0.3, pointRadius: 5, order: 0 },
                    { label: "Change in A/R", data: quarters.map((q) => q.x_change_ar), backgroundColor: C.teal, borderRadius: 5, order: 1, maxBarThickness: 34 },
                    { label: "Change in A/P", data: quarters.map((q) => q.x_change_ap), backgroundColor: C.amber, borderRadius: 5, order: 1, maxBarThickness: 34 },
                ],
            },
            options: this.baseOptions(this.clickable((i, ds) => this.drill(ds === 2 ? "x_change_ap" : "x_change_ar", quarters[i]))),
        });

        // 7. Top vendors
        const vendors = this.state.vendors.slice(0, 8);
        if (vendors.length) {
            this.make("vendors", {
                type: "bar",
                data: { labels: vendors.map((v) => v.x_name), datasets: [{ label: "Share of payables", data: vendors.map((v) => v.x_amount), backgroundColor: C.teal, borderRadius: 4, maxBarThickness: 22 }] },
                options: this.baseOptions({
                    ...this.clickable((i) => this.openVendor(vendors[i].x_name)),
                    indexAxis: "y",
                    plugins: Object.assign(this.baseOptions().plugins, { legend: { display: false } }),
                    scales: {
                        x: { grid: { color: C.grid }, border: { display: false }, ticks: { color: C.slate, callback: (v) => this.fmt(v, true) } },
                        y: { grid: { display: false }, ticks: { color: C.slate } },
                    },
                }),
            });
        }
    }
}

registry.category("actions").add("x_threshold_dashboard", ThresholdDashboard);
