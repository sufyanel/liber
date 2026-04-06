import base64
import io
from datetime import datetime, date

import xlsxwriter
from odoo import fields, models

BUDGET_LINE_TYPE_KEYS = (
    "cost_purchased_finished_goods",
    "variable_overhead_landed_costs",
    "add_back_fixed_overhead",
    "less_variable_operating_expense",
    "selling_general_administrative",
    "interest_expense",
    "taxes",
)


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

    def _get_quarter_date_range(self, year, quarter):
        if quarter == 1:
            return date(year, 1, 1), date(year, 3, 31)
        if quarter == 2:
            return date(year, 4, 1), date(year, 6, 30)
        if quarter == 3:
            return date(year, 7, 1), date(year, 9, 30)
        return date(year, 10, 1), date(year, 12, 31)

    def _get_sales_revenue_quarter_values(self, current_year):
        return self._get_values_for_period(
            {"04.1.101", "04.1.102", "04.1.104"},
            current_year,
            quarterly=True,
        )

    def _get_sales_revenue_year_values(self, current_year):
        return self._get_values_for_period(
            {"04.1.101", "04.1.102", "04.1.104"},
            current_year,
            quarterly=False,
        )

    def _get_cost_of_purchased_finished_goods_quarter_values(self, current_year):
        return self._get_values_for_period(
            {"05.1.101", "05.1.102", "05.1.103", "05.1.104", "05.1.105", "05.2.101", "05.2.102", "05.1.1.104", "500000"},
            current_year,
            quarterly=True,
        )

    def _get_cost_of_purchased_finished_goods_year_values(self, current_year):
        return self._get_values_for_period(
            {"05.1.101", "05.1.102", "05.1.103", "05.1.104", "05.1.105", "05.2.101", "05.2.102", "05.1.1.104", "500000"},
            current_year,
            quarterly=False,
        )

    def _get_variable_overhead_landed_costs_quarter_values(self, current_year):
        return self._get_values_for_period(
            {"05.1.113", "06.1.302", "05.1.106", "220110", "06.1.304", "220100"},
            current_year,
            quarterly=True,
        )

    def _get_variable_overhead_landed_costs_year_values(self, current_year):
        return self._get_values_for_period(
            {"05.1.113", "06.1.302", "05.1.106", "220110", "06.1.304", "220100"},
            current_year,
            quarterly=False,
        )

    def _get_add_back_fixed_overhead_quarter_values(self, current_year):
        return self._get_values_for_period(
            {"01.1.116", "230200", "06.2.505", "06.2.604", "220601", "06.2.605", "220600", "220900", "06.2.613"},
            current_year,
            quarterly=True,
        )

    def _get_add_back_fixed_overhead_year_values(self, current_year):
        return self._get_values_for_period(
            {"01.1.116", "230200", "06.2.505", "06.2.604", "220601", "06.2.605", "220600", "220900", "06.2.613"},
            current_year,
            quarterly=False,
        )

    def _get_less_variable_operating_expense_quarter_values(self, current_year):
        return self._get_values_for_period(
            {"06.2.611", "240101", "06.2.201", "212300", "06.2.503", "620000"},
            current_year,
            quarterly=True,
        )

    def _get_less_variable_operating_expense_year_values(self, current_year):
        return self._get_values_for_period(
            {"06.2.611", "240101", "06.2.201", "212300", "06.2.503", "620000"},
            current_year,
            quarterly=False,
        )

    def _get_interest_expense_quarter_values(self, current_year):
        return self._get_values_for_period(
            {"06.2.203"},
            current_year,
            quarterly=True,
        )

    def _get_interest_expense_year_values(self, current_year):
        return self._get_values_for_period(
            {"06.2.203"},
            current_year,
            quarterly=False,
        )

    def _get_taxes_quarter_values(self, current_year):
        return self._get_values_for_period(
            {"230150"},
            current_year,
            quarterly=True,
        )

    def _get_taxes_year_values(self, current_year):
        return self._get_values_for_period(
            {"230150"},
            current_year,
            quarterly=False,
        )

    def _aggregate_gl_for_accounts(self, target_account_ids, current_year, quarterly=True):
        selected_companies = self.company_ids
        if not selected_companies or not target_account_ids:
            return [0.0] * (20 if quarterly else 5)

        report = self.env.ref("account_reports.general_ledger_report").sudo().with_company(
            selected_companies[0]
        ).with_context(
            allowed_company_ids=selected_companies.ids
        )
        company_options = [{"id": company.id, "name": company.name} for company in selected_companies]
        values = []
        for year in range(current_year - 4, current_year + 1):
            period_quarters = range(1, 5) if quarterly else [None]
            for quarter in period_quarters:
                if year == current_year:
                    values.append(0.0)
                    continue
                if quarterly:
                    date_from, date_to = self._get_quarter_date_range(year, quarter)
                else:
                    date_from, date_to = date(year, 1, 1), date(year, 12, 31)
                previous_options = {
                    "date": {
                        "date_from": date_from.strftime("%Y-%m-%d"),
                        "date_to": date_to.strftime("%Y-%m-%d"),
                        "mode": "range",
                    },
                    "companies": company_options,
                }
                options = report.get_options(previous_options)
                lines = report._get_lines(options)
                balance_index = next(
                    (idx for idx, column in enumerate(options.get("columns", [])) if column.get("expression_label") == "balance"),
                    None,
                )
                value = 0.0
                seen_line_ids = set()
                for line in lines:
                    line_id = str(line.get("id") or "")
                    model, model_id = report._get_model_info_from_id(line_id)
                    if model != "account.account" or model_id not in target_account_ids:
                        continue
                    if line_id in seen_line_ids:
                        continue
                    columns = line.get("columns") or []
                    if balance_index is not None and balance_index < len(columns):
                        value += columns[balance_index].get("no_format", 0.0) or 0.0
                        seen_line_ids.add(line_id)
                values.append(value if value else 0.0)

        expected = 20 if quarterly else 5
        if len(values) < expected:
            values.extend([0.0] * (expected - len(values)))
        return values[:expected]

    def _get_values_for_period(self, account_codes, current_year, quarterly=True):
        selected_companies = self.company_ids
        if not selected_companies:
            return [0.0] * (20 if quarterly else 5)
        target_account_ids = set(
            self.env["account.account"].sudo().search([
                ("company_id", "in", selected_companies.ids),
                ("code", "in", list(account_codes)),
            ]).ids
        )
        return self._aggregate_gl_for_accounts(target_account_ids, current_year, quarterly)

    def _get_expense_type_account_quarter_values(self, current_year):
        selected_companies = self.company_ids
        if not selected_companies:
            return [0.0] * 20
        target_account_ids = set(
            self.env["account.account"].sudo().search([
                ("company_id", "in", selected_companies.ids),
                ("account_type", "=", "expense"),
            ]).ids
        )
        return self._aggregate_gl_for_accounts(target_account_ids, current_year, quarterly=True)

    def _get_expense_type_account_year_values(self, current_year):
        selected_companies = self.company_ids
        if not selected_companies:
            return [0.0] * 5
        target_account_ids = set(
            self.env["account.account"].sudo().search([
                ("company_id", "in", selected_companies.ids),
                ("account_type", "=", "expense"),
            ]).ids
        )
        return self._aggregate_gl_for_accounts(target_account_ids, current_year, quarterly=False)

    def _get_budget_line_amount(self, budget, line_type):
        if not budget:
            return 0.0
        line = budget.line_ids.filtered(lambda l: l.line_type == line_type)[:1]
        return float(line.amount or 0.0)

    def _budget_overlay_current_year(self, current_year, quarterly):
        Budget = self.env["income.statement.budget"].sudo()
        company_ids = self.company_ids.ids
        if not company_ids:
            segment_len = 4 if quarterly else 1
            empty = [0.0] * segment_len
            out = {"sales_revenue": list(empty)}
            for lt in BUDGET_LINE_TYPE_KEYS:
                out[lt] = list(empty)
            return out
        budgets = Budget.search([
            ("year", "=", str(current_year)),
            ("state", "=", "confirmed"),
            ("company_id", "in", company_ids),
        ])
        order = ("q1", "q2", "q3", "q4")
        out = {"sales_revenue": []}
        for lt in BUDGET_LINE_TYPE_KEYS:
            out[lt] = []
        if quarterly:
            for q in order:
                q_budgets = budgets.filtered(lambda b, qq=q: b.quarter == qq)
                out["sales_revenue"].append(
                    sum(float(b.sales_revenue or 0.0) for b in q_budgets)
                )
                for lt in BUDGET_LINE_TYPE_KEYS:
                    amt = sum(self._get_budget_line_amount(b, lt) for b in q_budgets)
                    if lt == "less_variable_operating_expense":
                        amt = -amt
                    if lt == "taxes":
                        amt = -amt
                    out[lt].append(amt)
        else:
            out["sales_revenue"].append(
                sum(float(b.sales_revenue or 0.0) for b in budgets)
            )
            for lt in BUDGET_LINE_TYPE_KEYS:
                amt = sum(self._get_budget_line_amount(b, lt) for b in budgets)
                if lt == "less_variable_operating_expense":
                    amt = -amt
                if lt == "taxes":
                    amt = -amt
                out[lt].append(amt)
        return out

    def _apply_budget_segment(self, values_list, segment, quarterly):
        if quarterly:
            if len(values_list) < 20 or len(segment) != 4:
                return values_list
            for i in range(4):
                values_list[16 + i] = segment[i]
        else:
            if len(values_list) < 5 or len(segment) != 1:
                return values_list
            values_list[4] = segment[0]
        return values_list

    def action_download_excel(self):
        current_year = int(self.year)
        year_labels = [
            f"Prior YR4 Actual ({current_year - 4})",
            f"Prior YR3 Actual ({current_year - 3})",
            f"Prior YR2 Actual ({current_year - 2})",
            f"Prior YR1 Actual ({current_year - 1})",
            f"Current YR Projected ({current_year})",
        ]
        companies = self.company_ids.sorted(key=lambda c: c.name)
        company_names = ", ".join(companies.mapped("name")) if companies else ""
        mode_label = dict(self._fields["report_mode"].selection).get(self.report_mode, self.report_mode)
        span_from = date(current_year - 4, 1, 1)
        span_to = date(current_year, 12, 31)
        if self.report_mode == "quarterly":
            period_body = (
                "Calendar quarters (Q1 Jan–Mar, Q2 Apr–Jun, Q3 Jul–Sep, Q4 Oct–Dec)."
            )
        else:
            period_body = (
                "One total per calendar year per column."
            )
        period_block = (
            "Report type: %s. Years shown: %s–%s. Column date span: %s to %s. %s"
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

        banner_title_format = workbook.add_format({
            "bold": True,
            "font_size": 20,
            "align": "center",
            "valign": "vcenter",
            "font_color": "#FFFFFF",
            "bg_color": "#1F4E79",
            "border": 1,
        })
        banner_sub_format = workbook.add_format({
            "bold": True,
            "font_size": 12,
            "align": "center",
            "valign": "vcenter",
            "font_color": "#1F4E79",
            "bg_color": "#E8F1FF",
            "border": 1,
        })
        meta_format = workbook.add_format({
            "font_size": 10,
            "align": "left",
            "valign": "vcenter",
            "text_wrap": True,
            "border": 1,
            "border_color": "#CED4DA",
            "bg_color": "#F8F9FA",
        })
        generated_format = workbook.add_format({
            "font_size": 9,
            "italic": True,
            "align": "left",
            "font_color": "#555555",
        })
        banner_rule_format = workbook.add_format({
            "bg_color": "#E67E22",
        })
        header_format = workbook.add_format({"bold": True, "align": "center", "border": 1})
        label_format = workbook.add_format({"bold": True, "align": "left", "border": 1})
        row_label_format = workbook.add_format({"align": "left", "border": 1})
        empty_cell_format = workbook.add_format({"border": 1})
        value_format = workbook.add_format({"align": "right", "border": 1, "num_format": "#,##0.00;[Red](#,##0.00);0.00"})

        worksheet.set_column("A:A", 40)
        if self.report_mode == "quarterly":
            last_col = 20
            worksheet.set_column("B:U", 14)
        else:
            last_col = 5
            worksheet.set_column("B:F", 22)

        hr = 0
        worksheet.merge_range(hr, 0, hr, last_col, "INCOME STATEMENT", banner_title_format)
        worksheet.set_row(hr, 34)
        hr += 1
        worksheet.merge_range(hr, 0, hr, last_col, mode_label.upper(), banner_sub_format)
        worksheet.set_row(hr, 24)
        hr += 1
        worksheet.merge_range(hr, 0, hr, last_col, "Companies: %s" % company_names, meta_format)
        worksheet.set_row(hr, 30 if len(company_names) > 100 else 20)
        hr += 1
        worksheet.merge_range(hr, 0, hr, last_col, period_block, meta_format)
        worksheet.set_row(hr, 48)
        hr += 1
        gen_ts = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        worksheet.merge_range(
            hr,
            0,
            hr,
            last_col,
            "Generated: %s" % gen_ts.strftime("%Y-%m-%d %H:%M %Z"),
            generated_format,
        )
        worksheet.set_row(hr, 16)
        hr += 1
        worksheet.merge_range(hr, 0, hr, last_col, "", banner_rule_format)
        worksheet.set_row(hr, 5)
        hr += 1

        col_header_row = hr
        if self.report_mode == "quarterly":
            worksheet.write(col_header_row, 0, "YR", header_format)
            start_col = 1
            for label in year_labels:
                end_col = start_col + 3
                worksheet.merge_range(col_header_row, start_col, col_header_row, end_col, label, header_format)
                qrow = col_header_row + 1
                worksheet.write(qrow, start_col, "Q1", header_format)
                worksheet.write(qrow, start_col + 1, "Q2", header_format)
                worksheet.write(qrow, start_col + 2, "Q3", header_format)
                worksheet.write(qrow, start_col + 3, "Q4", header_format)
                start_col += 4
            data_start_row = col_header_row + 2
            max_data_col = 20
        else:
            worksheet.write(col_header_row, 0, "YR", header_format)
            for idx, label in enumerate(year_labels, start=1):
                worksheet.write(col_header_row, idx, label, header_format)
            data_start_row = col_header_row + 1
            max_data_col = 5

        rows = [
            ("SALES REVENUE", True),
            ("Less Cost of Sales", True),
            ("Cost of Purchased Finished Goods", False),
            ("Variable Overhead Landed Costs", False),
            ("GROSS PROFIT MARGIN", True),
            ("Add back Fixed Overhead", False),
            ("Less Variable Operating Expense (xxx)", False),
            ("CONTRIBUTION MARGIN", True),
            ("Selling, General & Administrative", False),
            ("OPERATING PROFIT", True),
            ("Other income or expense:", True),
            ("Interest expense (xxx)", False),
            ("PROFIT BEFORE TAX", True),
            ("Taxes (xxx)", False),
            ("NET INCOME", True),
        ]

        row_by_label = {label: data_start_row + i for i, (label, _) in enumerate(rows)}

        row_index = data_start_row
        for label, is_bold in rows:
            format_for_label = label_format if is_bold else row_label_format
            worksheet.write(row_index, 0, label, format_for_label)
            for col_idx in range(1, max_data_col + 1):
                worksheet.write(row_index, col_idx, "", empty_cell_format)
            row_index += 1

        quarterly = self.report_mode == "quarterly"
        overlay = self._budget_overlay_current_year(current_year, quarterly)
        sales_revenue_values = (
            self._get_sales_revenue_quarter_values(current_year)
            if quarterly
            else self._get_sales_revenue_year_values(current_year)
        )
        self._apply_budget_segment(sales_revenue_values, overlay["sales_revenue"], quarterly)
        cost_purchased_finished_goods_values = (
            self._get_cost_of_purchased_finished_goods_quarter_values(current_year)
            if quarterly
            else self._get_cost_of_purchased_finished_goods_year_values(current_year)
        )
        self._apply_budget_segment(
            cost_purchased_finished_goods_values,
            overlay["cost_purchased_finished_goods"],
            quarterly,
        )
        variable_overhead_landed_costs_values = (
            self._get_variable_overhead_landed_costs_quarter_values(current_year)
            if quarterly
            else self._get_variable_overhead_landed_costs_year_values(current_year)
        )
        self._apply_budget_segment(
            variable_overhead_landed_costs_values,
            overlay["variable_overhead_landed_costs"],
            quarterly,
        )
        less_cost_of_sales_values = [
            (cost_purchased_finished_goods_values[idx] or 0.0) + (variable_overhead_landed_costs_values[idx] or 0.0)
            for idx in range(len(cost_purchased_finished_goods_values))
        ]
        gross_profit_margin_values = [
            (sales_revenue_values[idx] or 0.0) - (less_cost_of_sales_values[idx] or 0.0)
            for idx in range(len(sales_revenue_values))
        ]
        add_back_fixed_overhead_values = (
            self._get_add_back_fixed_overhead_quarter_values(current_year)
            if quarterly
            else self._get_add_back_fixed_overhead_year_values(current_year)
        )
        self._apply_budget_segment(
            add_back_fixed_overhead_values,
            overlay["add_back_fixed_overhead"],
            quarterly,
        )
        less_variable_operating_expense_raw = (
            self._get_less_variable_operating_expense_quarter_values(current_year)
            if quarterly
            else self._get_less_variable_operating_expense_year_values(current_year)
        )
        self._apply_budget_segment(
            less_variable_operating_expense_raw,
            overlay["less_variable_operating_expense"],
            quarterly,
        )
        less_variable_operating_expense_values = [
            -(value or 0.0) for value in less_variable_operating_expense_raw
        ]
        contribution_margin_values = [
            (gross_profit_margin_values[idx] or 0.0)
            + (add_back_fixed_overhead_values[idx] or 0.0)
            - (less_variable_operating_expense_values[idx] or 0.0)
            for idx in range(len(gross_profit_margin_values))
        ]
        interest_expense_values = (
            self._get_interest_expense_quarter_values(current_year)
            if quarterly
            else self._get_interest_expense_year_values(current_year)
        )
        self._apply_budget_segment(interest_expense_values, overlay["interest_expense"], quarterly)
        selling_general_administrative_values = (
            self._get_expense_type_account_quarter_values(current_year)
            if quarterly
            else self._get_expense_type_account_year_values(current_year)
        )
        self._apply_budget_segment(
            selling_general_administrative_values,
            overlay["selling_general_administrative"],
            quarterly,
        )
        operating_profit_values = [
            (contribution_margin_values[idx] or 0.0) - (selling_general_administrative_values[idx] or 0.0)
            for idx in range(len(contribution_margin_values))
        ]
        profit_before_tax_values = [
            (operating_profit_values[idx] or 0.0) - (interest_expense_values[idx] or 0.0)
            for idx in range(len(operating_profit_values))
        ]
        taxes_values = (
            self._get_taxes_quarter_values(current_year)
            if quarterly
            else self._get_taxes_year_values(current_year)
        )
        self._apply_budget_segment(taxes_values, overlay["taxes"], quarterly)
        net_income_values = [
            (profit_before_tax_values[idx] or 0.0) + (taxes_values[idx] or 0.0)
            for idx in range(len(profit_before_tax_values))
        ]
        for col_idx, value in enumerate(sales_revenue_values, start=1):
            worksheet.write(row_by_label["SALES REVENUE"], col_idx, value, value_format)
        for col_idx, value in enumerate(less_cost_of_sales_values, start=1):
            worksheet.write(row_by_label["Less Cost of Sales"], col_idx, value, value_format)
        for col_idx, value in enumerate(cost_purchased_finished_goods_values, start=1):
            worksheet.write(row_by_label["Cost of Purchased Finished Goods"], col_idx, value, value_format)
        for col_idx, value in enumerate(variable_overhead_landed_costs_values, start=1):
            worksheet.write(row_by_label["Variable Overhead Landed Costs"], col_idx, value, value_format)
        for col_idx, value in enumerate(gross_profit_margin_values, start=1):
            worksheet.write(row_by_label["GROSS PROFIT MARGIN"], col_idx, value, value_format)
        for col_idx, value in enumerate(add_back_fixed_overhead_values, start=1):
            worksheet.write(row_by_label["Add back Fixed Overhead"], col_idx, value, value_format)
        for col_idx, value in enumerate(less_variable_operating_expense_values, start=1):
            worksheet.write(row_by_label["Less Variable Operating Expense (xxx)"], col_idx, value, value_format)
        for col_idx, value in enumerate(contribution_margin_values, start=1):
            worksheet.write(row_by_label["CONTRIBUTION MARGIN"], col_idx, value, value_format)
        for col_idx, value in enumerate(selling_general_administrative_values, start=1):
            worksheet.write(row_by_label["Selling, General & Administrative"], col_idx, value, value_format)
        for col_idx, value in enumerate(operating_profit_values, start=1):
            worksheet.write(row_by_label["OPERATING PROFIT"], col_idx, value, value_format)
        for col_idx, value in enumerate(interest_expense_values, start=1):
            worksheet.write(row_by_label["Interest expense (xxx)"], col_idx, value, value_format)
        for col_idx, value in enumerate(profit_before_tax_values, start=1):
            worksheet.write(row_by_label["PROFIT BEFORE TAX"], col_idx, value, value_format)
        for col_idx, value in enumerate(taxes_values, start=1):
            worksheet.write(row_by_label["Taxes (xxx)"], col_idx, value, value_format)
        for col_idx, value in enumerate(net_income_values, start=1):
            worksheet.write(row_by_label["NET INCOME"], col_idx, value, value_format)

        workbook.close()
        output.seek(0)

        attachment = self.env["ir.attachment"].create(
            {
                "name": f"Income_Statement_{current_year}.xlsx",
                "type": "binary",
                "datas": base64.b64encode(output.read()),
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
        )

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }
