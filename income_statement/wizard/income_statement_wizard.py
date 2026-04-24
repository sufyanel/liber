import base64
import io
from datetime import datetime, date

import xlsxwriter
from odoo import fields, models

ACCOUNT_CODE_MAP = {
    "sales_revenue": {
        "04.1.101", "04.1.102", "04.1.104",
    },
    "cost_purchased_finished_goods": {
        "05.1.101", "05.1.102", "05.1.103", "05.1.104", "05.1.105",
        "05.2.101", "05.2.102", "05.1.1.104", "500000",
    },
    "variable_overhead_landed_costs": {
        "05.1.113", "06.1.302", "05.1.106", "220110", "06.1.304", "220100",
    },
    "add_back_fixed_overhead": {
        "01.1.116", "230200", "06.2.505", "06.2.604",
        "220601", "06.2.605", "220600", "220900", "06.2.613",
    },
    "less_variable_operating_expense": {
        "06.2.611", "240101", "06.2.201", "212300", "06.2.503", "620000",
    },
    "interest_expense": {"06.2.203"},
    "taxes": {"230150"},
}

BUDGET_LINE_TYPE_KEYS = (
    "cost_purchased_finished_goods",
    "variable_overhead_landed_costs",
    "add_back_fixed_overhead",
    "less_variable_operating_expense",
    "selling_general_administrative",
    "interest_expense",
    "taxes",
)

NEGATE_DISPLAY = frozenset({
    "less_cost_of_sales",
    "cost_purchased_finished_goods",
    "variable_overhead_landed_costs",
    "less_variable_operating_expense",
    "selling_general_administrative",
    "interest_expense",
    "taxes",
})

ROW_SPEC = [
    ("SALES REVENUE", "sales_revenue", True),
    ("Less Cost of Sales", "less_cost_of_sales", True),
    ("Cost of Purchased Finished Goods", "cost_purchased_finished_goods", False),
    ("Variable Overhead Landed Costs", "variable_overhead_landed_costs", False),
    ("GROSS PROFIT MARGIN", "gross_profit_margin", True),
    ("Add back Fixed Overhead", "add_back_fixed_overhead", False),
    ("Less Variable Operating Expense", "less_variable_operating_expense", False),
    ("CONTRIBUTION MARGIN", "contribution_margin", True),
    ("Selling, General & Administrative", "selling_general_administrative", False),
    ("OPERATING PROFIT", "operating_profit", True),
    ("Other income or expense", "other_income_expense", True),
    ("Interest expense", "interest_expense", False),
    ("PROFIT BEFORE TAX", "profit_before_tax", True),
    ("Taxes", "taxes", False),
    ("NET INCOME", "net_income", True),
]


class IncomeStatementWizard(models.TransientModel):
    _name = "income.statement.wizard"
    _description = "Income Statement Wizard"

    company_ids = fields.Many2many("res.company", string="Companies", required=True)
    report_mode = fields.Selection(
        [("quarterly", "Quarterly"), ("yearly", "Yearly")],
        string="Report Type",
        required=True,
        default="quarterly",
    )
    year = fields.Selection(
        selection=lambda self: self._get_year_selection(),
        string="Current Year",
        required=True,
        default=lambda self: str(datetime.now().year),
    )

    def _get_year_selection(self):
        current_year = datetime.now().year
        return [(str(y), str(y)) for y in range(current_year - 4, current_year + 1)]

    def _resolve_accounts(self):
        Account = self.env["account.account"].sudo()
        Mapping = self.env["income.statement.account.mapping"].sudo()
        company_ids = self.company_ids.ids
        if not company_ids:
            return {}, set(), set()

        all_mappings = Mapping.search([("company_id", "in", company_ids)])
        mapping_lookup = {}
        for m in all_mappings:
            mapping_lookup.setdefault(m.row_key, set()).update(m.account_ids.ids)

        row_account_ids = {}
        all_mapped_ids = set()
        for row_key, default_codes in ACCOUNT_CODE_MAP.items():
            if row_key in mapping_lookup:
                ids = mapping_lookup[row_key]
            else:
                ids = set(
                    Account.search([
                        ("company_id", "in", company_ids),
                        ("code", "in", list(default_codes)),
                    ]).ids
                )
            row_account_ids[row_key] = ids
            all_mapped_ids |= ids

        sga_accounts = Account.search([
            ("company_id", "in", company_ids),
            ("account_type", "=", "expense"),
            ("id", "not in", list(all_mapped_ids)),
        ])
        row_account_ids["selling_general_administrative"] = set(sga_accounts.ids)
        all_mapped_ids |= row_account_ids["selling_general_administrative"]

        other_accounts = Account.search([
            ("company_id", "in", company_ids),
            ("account_type", "=", "income_other"),
        ])
        row_account_ids["other_income_expense"] = set(other_accounts.ids)
        all_mapped_ids |= row_account_ids["other_income_expense"]

        income_account_ids = set(Account.search([
            ("id", "in", list(all_mapped_ids)),
            ("account_type", "in", ("income", "income_other")),
        ]).ids)

        return row_account_ids, all_mapped_ids, income_account_ids

    def _fetch_gl_balances(self, all_account_ids, current_year):
        if not all_account_ids or not self.company_ids:
            return {}

        self.env.cr.execute(
            """
            SELECT
                aml.account_id,
                EXTRACT(YEAR FROM aml.date)::int,
                EXTRACT(QUARTER FROM aml.date)::int,
                SUM(aml.balance)
            FROM account_move_line aml
            WHERE aml.account_id = ANY(%(aids)s)
              AND aml.company_id = ANY(%(cids)s)
              AND aml.date >= %(d0)s
              AND aml.date <= %(d1)s
              AND aml.parent_state = 'posted'
            GROUP BY aml.account_id,
                     EXTRACT(YEAR FROM aml.date)::int,
                     EXTRACT(QUARTER FROM aml.date)::int
            """,
            {
                "aids": list(all_account_ids),
                "cids": self.company_ids.ids,
                "d0": date(current_year - 4, 1, 1),
                "d1": date(current_year, 12, 31),
            },
        )

        balances = {}
        for account_id, yr, qtr, bal in self.env.cr.fetchall():
            balances[(account_id, int(yr), int(qtr))] = bal or 0.0
        return balances

    def _build_actuals(self, row_account_ids, income_ids, balances, current_year, quarterly):
        years = range(current_year - 4, current_year + 1)
        result = {}
        for row_key, account_ids in row_account_ids.items():
            values = []
            for yr in years:
                if quarterly:
                    for q in range(1, 5):
                        val = 0.0
                        for aid in account_ids:
                            raw = balances.get((aid, yr, q), 0.0)
                            if aid in income_ids:
                                raw = -raw
                            val += raw
                        values.append(val)
                else:
                    val = 0.0
                    for aid in account_ids:
                        for q in range(1, 5):
                            raw = balances.get((aid, yr, q), 0.0)
                            if aid in income_ids:
                                raw = -raw
                            val += raw
                    values.append(val)
            result[row_key] = values
        return result

    def _build_budget_values(self, current_year, quarterly):
        n = 4 if quarterly else 1
        empty = {"sales_revenue": [0.0] * n, "other_income_expense": [0.0] * n}
        for lt in BUDGET_LINE_TYPE_KEYS:
            empty[lt] = [0.0] * n

        company_ids = self.company_ids.ids
        if not company_ids:
            return empty

        budgets = self.env["income.statement.budget"].sudo().search([
            ("year", "=", str(current_year)),
            ("state", "=", "confirmed"),
            ("company_id", "in", company_ids),
        ])
        if not budgets:
            return empty

        out = {"sales_revenue": [], "other_income_expense": [0.0] * n}
        for lt in BUDGET_LINE_TYPE_KEYS:
            out[lt] = []

        quarters = ("q1", "q2", "q3", "q4") if quarterly else (None,)
        for q in quarters:
            q_budgets = budgets.filtered(lambda b, qq=q: b.quarter == qq) if q else budgets
            out["sales_revenue"].append(
                sum(float(b.sales_revenue or 0.0) for b in q_budgets)
            )
            for lt in BUDGET_LINE_TYPE_KEYS:
                amt = 0.0
                for b in q_budgets:
                    bl = b.line_ids.filtered(lambda l, t=lt: l.line_type == t)[:1]
                    if bl:
                        amt += float(bl.amount or 0.0)
                out[lt].append(amt)
        return out

    def _compute_derived(self, base, n):
        z = [0.0] * n
        sales = base.get("sales_revenue", z)
        copfg = base.get("cost_purchased_finished_goods", z)
        var_oh = base.get("variable_overhead_landed_costs", z)
        fixed_oh = base.get("add_back_fixed_overhead", z)
        var_opex = base.get("less_variable_operating_expense", z)
        sga = base.get("selling_general_administrative", z)
        other_ie = base.get("other_income_expense", z)
        interest = base.get("interest_expense", z)
        taxes = base.get("taxes", z)

        less_cos = [a + b for a, b in zip(copfg, var_oh)]
        gpm = [s - c for s, c in zip(sales, less_cos)]
        cm = [g + f - v for g, f, v in zip(gpm, fixed_oh, var_opex)]
        op = [c - s for c, s in zip(cm, sga)]
        pbt = [o + oi - i for o, oi, i in zip(op, other_ie, interest)]
        ni = [p - t for p, t in zip(pbt, taxes)]

        base["less_cost_of_sales"] = less_cos
        base["gross_profit_margin"] = gpm
        base["contribution_margin"] = cm
        base["operating_profit"] = op
        base["profit_before_tax"] = pbt
        base["net_income"] = ni

    def action_download_excel(self):
        current_year = int(self.year)
        quarterly = self.report_mode == "quarterly"
        n_actual = 20 if quarterly else 5
        n_budget = 4 if quarterly else 1

        row_account_ids, all_account_ids, income_ids = self._resolve_accounts()
        balances = self._fetch_gl_balances(all_account_ids, current_year)
        actuals = self._build_actuals(row_account_ids, income_ids, balances, current_year, quarterly)
        self._compute_derived(actuals, n_actual)

        budget_base = self._build_budget_values(current_year, quarterly)
        self._compute_derived(budget_base, n_budget)

        year_labels = [
            "Prior YR4 Actual (%d)" % (current_year - 4),
            "Prior YR3 Actual (%d)" % (current_year - 3),
            "Prior YR2 Actual (%d)" % (current_year - 2),
            "Prior YR1 Actual (%d)" % (current_year - 1),
            "Current YR Actual (%d)" % current_year,
            "Current YR Budget (%d)" % current_year,
        ]

        companies = self.company_ids.sorted(key=lambda c: c.name)
        company_names = ", ".join(companies.mapped("name")) if companies else ""
        mode_label = dict(self._fields["report_mode"].selection).get(
            self.report_mode, self.report_mode
        )
        span_from = date(current_year - 4, 1, 1)
        span_to = date(current_year, 12, 31)
        if quarterly:
            period_body = "Calendar quarters (Q1 Jan-Mar, Q2 Apr-Jun, Q3 Jul-Sep, Q4 Oct-Dec)."
        else:
            period_body = "One total per calendar year per column."
        period_block = (
            "Report type: %s. Years shown: %d-%d. Column date span: %s to %s. %s"
            % (
                mode_label,
                current_year - 4,
                current_year,
                span_from.isoformat(),
                span_to.isoformat(),
                period_body,
            )
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Income Statement")

        banner_title_fmt = workbook.add_format({
            "bold": True, "font_size": 20, "align": "center", "valign": "vcenter",
            "font_color": "#FFFFFF", "bg_color": "#1F4E79", "border": 1,
        })
        banner_sub_fmt = workbook.add_format({
            "bold": True, "font_size": 12, "align": "center", "valign": "vcenter",
            "font_color": "#1F4E79", "bg_color": "#E8F1FF", "border": 1,
        })
        meta_fmt = workbook.add_format({
            "font_size": 10, "align": "left", "valign": "vcenter", "text_wrap": True,
            "border": 1, "border_color": "#CED4DA", "bg_color": "#F8F9FA",
        })
        gen_fmt = workbook.add_format({
            "font_size": 9, "italic": True, "align": "left", "font_color": "#555555",
        })
        rule_fmt = workbook.add_format({"bg_color": "#E67E22"})
        hdr_fmt = workbook.add_format({"bold": True, "align": "center", "border": 1})
        lbl_fmt = workbook.add_format({"bold": True, "align": "left", "border": 1})
        row_lbl_fmt = workbook.add_format({"align": "left", "border": 1})
        empty_fmt = workbook.add_format({"border": 1})
        val_fmt = workbook.add_format({
            "align": "right", "border": 1,
            "num_format": "#,##0.00;[Red](#,##0.00);0.00",
        })

        if quarterly:
            last_col = n_actual + n_budget
            worksheet.set_column("A:A", 40)
            worksheet.set_column(1, last_col, 14)
        else:
            last_col = n_actual + n_budget
            worksheet.set_column("A:A", 40)
            worksheet.set_column(1, last_col, 22)

        hr = 0
        worksheet.merge_range(hr, 0, hr, last_col, "INCOME STATEMENT", banner_title_fmt)
        worksheet.set_row(hr, 34)
        hr += 1
        worksheet.merge_range(hr, 0, hr, last_col, mode_label.upper(), banner_sub_fmt)
        worksheet.set_row(hr, 24)
        hr += 1
        worksheet.merge_range(
            hr, 0, hr, last_col, "Companies: %s" % company_names, meta_fmt
        )
        worksheet.set_row(hr, 30 if len(company_names) > 100 else 20)
        hr += 1
        worksheet.merge_range(hr, 0, hr, last_col, period_block, meta_fmt)
        worksheet.set_row(hr, 48)
        hr += 1
        gen_ts = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        worksheet.merge_range(
            hr, 0, hr, last_col,
            "Generated: %s" % gen_ts.strftime("%Y-%m-%d %H:%M %Z"),
            gen_fmt,
        )
        worksheet.set_row(hr, 16)
        hr += 1
        worksheet.merge_range(hr, 0, hr, last_col, "", rule_fmt)
        worksheet.set_row(hr, 5)
        hr += 1

        col_hdr_row = hr
        if quarterly:
            worksheet.write(col_hdr_row, 0, "YR", hdr_fmt)
            col = 1
            for label in year_labels:
                worksheet.merge_range(
                    col_hdr_row, col, col_hdr_row, col + 3, label, hdr_fmt
                )
                qrow = col_hdr_row + 1
                for qi, ql in enumerate(("Q1", "Q2", "Q3", "Q4")):
                    worksheet.write(qrow, col + qi, ql, hdr_fmt)
                col += 4
            data_start = col_hdr_row + 2
        else:
            worksheet.write(col_hdr_row, 0, "YR", hdr_fmt)
            for idx, label in enumerate(year_labels, start=1):
                worksheet.write(col_hdr_row, idx, label, hdr_fmt)
            data_start = col_hdr_row + 1

        for i, (label, key, bold) in enumerate(ROW_SPEC):
            row = data_start + i
            worksheet.write(row, 0, label, lbl_fmt if bold else row_lbl_fmt)
            for c in range(1, last_col + 1):
                worksheet.write(row, c, "", empty_fmt)

            actual_vals = actuals.get(key, [0.0] * n_actual)
            budget_vals = budget_base.get(key, [0.0] * n_budget)
            sign = -1 if key in NEGATE_DISPLAY else 1

            for ci, val in enumerate(actual_vals):
                worksheet.write(row, 1 + ci, val * sign, val_fmt)
            for ci, val in enumerate(budget_vals):
                worksheet.write(row, 1 + n_actual + ci, val * sign, val_fmt)

        workbook.close()
        output.seek(0)

        attachment = self.env["ir.attachment"].create({
            "name": "Income_Statement_%d.xlsx" % current_year,
            "type": "binary",
            "datas": base64.b64encode(output.read()),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%d?download=true" % attachment.id,
            "target": "self",
        }
