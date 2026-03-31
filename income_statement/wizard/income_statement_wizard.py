import base64
import io
from datetime import datetime, date

import xlsxwriter
from odoo import fields, models


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

    def _get_values_for_period(self, account_codes, current_year, quarterly=True):
        selected_companies = self.company_ids
        if not selected_companies:
            return [0.0] * (20 if quarterly else 5)

        report = self.env.ref("account_reports.general_ledger_report").sudo().with_company(
            selected_companies[0]
        ).with_context(
            allowed_company_ids=selected_companies.ids
        )
        target_account_ids = set(
            self.env["account.account"].sudo().search([
                ("company_id", "in", selected_companies.ids),
                ("code", "in", list(account_codes)),
            ]).ids
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

    def action_download_excel(self):
        current_year = int(self.year)
        year_labels = [
            f"Prior YR4 Actual ({current_year - 4})",
            f"Prior YR3 Actual ({current_year - 3})",
            f"Prior YR2 Actual ({current_year - 2})",
            f"Prior YR1 Actual ({current_year - 1})",
            f"Current YR Projected ({current_year})",
        ]
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Income Statement")

        title_format = workbook.add_format({"bold": True, "font_size": 14, "align": "left"})
        header_format = workbook.add_format({"bold": True, "align": "center", "border": 1})
        label_format = workbook.add_format({"bold": True, "align": "left", "border": 1})
        row_label_format = workbook.add_format({"align": "left", "border": 1})
        empty_cell_format = workbook.add_format({"border": 1})
        value_format = workbook.add_format({"align": "right", "border": 1, "num_format": "#,##0.00;[Red](#,##0.00);0.00"})

        worksheet.set_column("A:A", 38)
        if self.report_mode == "quarterly":
            worksheet.set_column("B:U", 14)
            worksheet.merge_range("A1:U1", "INCOME STATEMENT", title_format)
            worksheet.write(2, 0, "YR", header_format)
            start_col = 1
            for label in year_labels:
                end_col = start_col + 3
                worksheet.merge_range(2, start_col, 2, end_col, label, header_format)
                worksheet.write(3, start_col, "Q1", header_format)
                worksheet.write(3, start_col + 1, "Q2", header_format)
                worksheet.write(3, start_col + 2, "Q3", header_format)
                worksheet.write(3, start_col + 3, "Q4", header_format)
                start_col += 4
            data_start_row = 4
            max_data_col = 20
        else:
            worksheet.set_column("B:F", 22)
            worksheet.merge_range("A1:F1", "INCOME STATEMENT", title_format)
            worksheet.write(2, 0, "YR", header_format)
            for idx, label in enumerate(year_labels, start=1):
                worksheet.write(2, idx, label, header_format)
            data_start_row = 3
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

        row_index = data_start_row
        for label, is_bold in rows:
            format_for_label = label_format if is_bold else row_label_format
            worksheet.write(row_index, 0, label, format_for_label)
            for col_idx in range(1, max_data_col + 1):
                worksheet.write(row_index, col_idx, "", empty_cell_format)
            row_index += 1

        sales_revenue_values = (
            self._get_sales_revenue_quarter_values(current_year)
            if self.report_mode == "quarterly"
            else self._get_sales_revenue_year_values(current_year)
        )
        cost_purchased_finished_goods_values = (
            self._get_cost_of_purchased_finished_goods_quarter_values(current_year)
            if self.report_mode == "quarterly"
            else self._get_cost_of_purchased_finished_goods_year_values(current_year)
        )
        variable_overhead_landed_costs_values = (
            self._get_variable_overhead_landed_costs_quarter_values(current_year)
            if self.report_mode == "quarterly"
            else self._get_variable_overhead_landed_costs_year_values(current_year)
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
            if self.report_mode == "quarterly"
            else self._get_add_back_fixed_overhead_year_values(current_year)
        )
        less_variable_operating_expense_values = (
            self._get_less_variable_operating_expense_quarter_values(current_year)
            if self.report_mode == "quarterly"
            else self._get_less_variable_operating_expense_year_values(current_year)
        )
        less_variable_operating_expense_values = [-(value or 0.0) for value in less_variable_operating_expense_values]
        contribution_margin_values = [
            (gross_profit_margin_values[idx] or 0.0)
            + (add_back_fixed_overhead_values[idx] or 0.0)
            - (less_variable_operating_expense_values[idx] or 0.0)
            for idx in range(len(gross_profit_margin_values))
        ]
        interest_expense_values = (
            self._get_interest_expense_quarter_values(current_year)
            if self.report_mode == "quarterly"
            else self._get_interest_expense_year_values(current_year)
        )
        sales_revenue_row = data_start_row
        for col_idx, value in enumerate(sales_revenue_values, start=1):
            worksheet.write(sales_revenue_row, col_idx, value, value_format)
        less_cost_of_sales_row = data_start_row + 1
        for col_idx, value in enumerate(less_cost_of_sales_values, start=1):
            worksheet.write(less_cost_of_sales_row, col_idx, value, value_format)
        cost_purchased_finished_goods_row = data_start_row + 2
        for col_idx, value in enumerate(cost_purchased_finished_goods_values, start=1):
            worksheet.write(cost_purchased_finished_goods_row, col_idx, value, value_format)
        variable_overhead_landed_costs_row = data_start_row + 3
        for col_idx, value in enumerate(variable_overhead_landed_costs_values, start=1):
            worksheet.write(variable_overhead_landed_costs_row, col_idx, value, value_format)
        gross_profit_margin_row = data_start_row + 4
        for col_idx, value in enumerate(gross_profit_margin_values, start=1):
            worksheet.write(gross_profit_margin_row, col_idx, value, value_format)
        add_back_fixed_overhead_row = data_start_row + 5
        for col_idx, value in enumerate(add_back_fixed_overhead_values, start=1):
            worksheet.write(add_back_fixed_overhead_row, col_idx, value, value_format)
        less_variable_operating_expense_row = data_start_row + 6
        for col_idx, value in enumerate(less_variable_operating_expense_values, start=1):
            worksheet.write(less_variable_operating_expense_row, col_idx, value, value_format)
        contribution_margin_row = data_start_row + 7
        for col_idx, value in enumerate(contribution_margin_values, start=1):
            worksheet.write(contribution_margin_row, col_idx, value, value_format)
        interest_expense_row = data_start_row + 11
        for col_idx, value in enumerate(interest_expense_values, start=1):
            worksheet.write(interest_expense_row, col_idx, value, value_format)

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
