import base64
import io
from collections import defaultdict
from datetime import datetime, date

import xlsxwriter
from dateutil.relativedelta import relativedelta
from odoo import _, models, fields, api
from odoo.exceptions import UserError


class ThresholdReportWizard(models.TransientModel):
    _name = 'threshold.report.wizard'
    _description = 'Threshold Report Wizard'

    company_id = fields.Many2one('res.company', string='Company')
    capital_investments = fields.Float(string='Capital Investments', default=100000.0)
    savings = fields.Float(string='Savings', default=50000.0)
    investor_return = fields.Float(string='Investor Return', default=0.0)
    tax = fields.Float(string='Tax', default=0.0)

    duration = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year')
    ], string='Duration', required=True, default='year')

    year = fields.Selection(selection='_get_year_selection', string='Year',
                            default=lambda self: str(datetime.now().year))
    quarter = fields.Selection(selection='_get_quarter_selection', string='Quarter')
    month = fields.Selection(selection='_get_month_selection', string='Month')

    @api.model
    def _get_year_selection(self):
        """Return years from 2019 to current year"""

        current_year = datetime.now().year
        return [(str(year), str(year)) for year in range(2022, current_year + 1)]

    @api.model
    def _get_quarter_selection(self):
        """Return quarters based on current year selection"""
        current_year = datetime.now().year
        current_quarter = (datetime.now().month - 1) // 3 + 1

        quarters = [
            ('Q1', 'Q1 (Jan-Mar)'),
            ('Q2', 'Q2 (Apr-Jun)'),
            ('Q3', 'Q3 (Jul-Sep)'),
            ('Q4', 'Q4 (Oct-Dec)')
        ]

        # If selected year is current year, only show quarters up to current quarter
        if hasattr(self, 'year') and self.year and int(self.year) == current_year:
            return quarters[:current_quarter]

        return quarters

    @api.model
    def _get_month_selection(self):
        """Return months based on current year selection"""
        current_year = datetime.now().year
        current_month = datetime.now().month

        months = [
            ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'),
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]

        # If selected year is current year, only show months up to current month
        if hasattr(self, 'year') and self.year and int(self.year) == current_year:
            return months[:current_month]

        return months

    @api.onchange('year')
    def _onchange_year(self):
        """Reset quarter and month when year changes"""

        self.quarter = False
        self.month = False

    @api.onchange('duration')
    def _onchange_duration(self):
        if self.duration == 'year':
            self.quarter = False
            self.month = False
        elif self.duration == 'quarter':
            self.month = False
        elif self.duration == 'month':
            self.quarter = False

    def _get_date_range(self):
        """Calculate date range based on duration selection"""
        if self.duration == 'year':
            year = int(self.year) if self.year else datetime.now().year
            return date(year, 1, 1), date(year, 12, 31)
        elif self.duration == 'quarter':
            year = int(self.year) if self.year else datetime.now().year
            quarter_months = {
                'Q1': (1, 3), 'Q2': (4, 6), 'Q3': (7, 9), 'Q4': (10, 12)
            }
            start_month, end_month = quarter_months[self.quarter]
            return date(year, start_month, 1), date(year, end_month, 1) + relativedelta(months=1) - relativedelta(
                days=1)
        elif self.duration == 'month':
            year = int(self.year) if self.year else datetime.now().year
            month = int(self.month)
            start_date = date(year, month, 1)
            end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
            return start_date, end_date

    def action_download_excel(self):
        # Validate required fields based on duration
        if self.duration == 'year' and not self.year:
            raise UserError(_('Please select a year.'))
        elif self.duration == 'quarter' and (not self.year or not self.quarter):
            raise UserError(_('Please select a year and quarter.'))
        elif self.duration == 'month' and (not self.year or not self.month):
            raise UserError(_('Please select a year and month.'))

        data = self._get_threshold_data()
        return self._download_excel(data)

    def _get_threshold_data(self):
        """Calculate all threshold report values"""

        # Get date range based on selection
        date_from, date_to = self._get_date_range()

        data = {
            'date_from': date_from,
            'date_to': date_to
        }

        # Get salary
        data['salary'] = self._get_mapping_amount('salary')

        # Taxes: mapping if one is configured, else the wizard's manual input
        data['taxes'] = self._get_mapping_amount_or_default('taxes', self.tax or 0.0)

        # Get net profit and calculate PBT
        net_profit = self._get_net_profit()
        data['pbt'] = net_profit

        data['depreciation'] = self._get_mapping_amount('depreciation')

        # Capital investments: mapping if one is configured, else the wizard's manual input
        data['capital_investments'] = self._get_mapping_amount_or_default(
            'capital_investments', self.capital_investments
        )

        # Change in A/R (closing balance minus opening balance over the mapped accounts)
        data['change_ar'] = self._get_mapping_balance_change('change_ar')

        data['change_payables'] = self._get_mapping_payables_amount('change_payables')

        # Change Net Change in A/R and A/P
        data['change_payables_receivable'] = data['change_ar'] + data['change_payables']

        # Change in Inventory (closing balance minus opening balance over the mapped accounts)
        data['change_inventory'] = self._get_mapping_balance_change('change_inventory')

        data['debt_retirement'] = self._get_mapping_amount('debt_retirement')

        # Investor Return: mapping if one is configured, else the wizard's manual input
        data['investor_return_total'] = self._get_mapping_amount_or_default(
            'investor_return', self.investor_return
        )

        # Savings: mapping if one is configured, else the wizard's manual input
        data['savings'] = self._get_mapping_amount_or_default('savings', self.savings)

        # Calculate Financial Security Threshold
        data['financial_threshold'] = self._calculate_threshold(data)

        return data

    def _get_mapping(self, row_key, company=None):
        """Return the threshold report account mapping for row_key/company, if any."""
        company = company or self.company_id
        if not company:
            return self.env['threshold.report.account.mapping']
        return self.env['threshold.report.account.mapping'].sudo().search([
            ('company_id', '=', company.id),
            ('row_key', '=', row_key),
        ], limit=1)

    def _get_mapping_amount_or_default(self, row_key, default, date_from=None, date_to=None, company=None):
        """Like _get_mapping_amount, but for the wizard's manual-input rows
        (capital investments, savings, taxes, investor return): when no
        mapping row exists at all for this company/row_key, fall back to the
        wizard's own field value instead of 0.0. When a mapping row does
        exist, it is authoritative even if it computes to 0."""
        company = company or self.company_id
        if not company:
            return default
        if not self._get_mapping(row_key, company):
            return default
        return self._get_mapping_amount(row_key, date_from=date_from, date_to=date_to, company=company)

    def _get_mapping_amount(self, row_key, date_from=None, date_to=None, company=None):
        """Sum posted move line balances for the row's mapped accounts, weighted by
        each line's percentage. Falls back to the mapping's manual amount when no
        account lines are configured."""
        company = company or self.company_id
        if not company:
            return 0.0
        if not date_from or not date_to:
            date_from, date_to = self._get_date_range()

        mapping = self._get_mapping(row_key, company)
        if not mapping:
            return 0.0
        if not mapping.line_ids:
            return mapping.amount or 0.0

        groups = self.env['account.move.line'].sudo().read_group(
            [
                ('account_id', 'in', mapping.line_ids.account_id.ids),
                ('date', '>=', date_from),
                ('date', '<=', date_to),
                ('move_id.state', '=', 'posted'),
            ],
            ['balance:sum'],
            ['account_id'],
        )
        balance_by_account = {g['account_id'][0]: g['balance'] for g in groups}

        total = 0.0
        for line in mapping.line_ids:
            balance = balance_by_account.get(line.account_id.id, 0.0)
            total += balance * (line.percentage or 0.0) / 100.0
        return total

    def _get_mapping_balance_change(self, row_key, company=None):
        """Return the closing-minus-opening balance change over the row's mapped
        accounts, weighted by each line's percentage. Falls back to the mapping's
        manual amount when no account lines are configured."""
        company = company or self.company_id
        if not company:
            return 0.0

        mapping = self._get_mapping(row_key, company)
        if not mapping:
            return 0.0
        if not mapping.line_ids:
            return mapping.amount or 0.0

        date_from, date_to = self._get_date_range()
        opening_date = date_from - relativedelta(days=1)
        account_ids = mapping.line_ids.account_id.ids
        MoveLine = self.env['account.move.line'].sudo()

        opening_by_account = {
            g['account_id'][0]: g['balance']
            for g in MoveLine.read_group(
                [
                    ('account_id', 'in', account_ids),
                    ('date', '<=', opening_date),
                    ('move_id.state', '=', 'posted'),
                ],
                ['balance:sum'],
                ['account_id'],
            )
        }
        closing_by_account = {
            g['account_id'][0]: g['balance']
            for g in MoveLine.read_group(
                [
                    ('account_id', 'in', account_ids),
                    ('date', '<=', date_to),
                    ('move_id.state', '=', 'posted'),
                ],
                ['balance:sum'],
                ['account_id'],
            )
        }

        total = 0.0
        for line in mapping.line_ids:
            change = closing_by_account.get(line.account_id.id, 0.0) - opening_by_account.get(line.account_id.id, 0.0)
            total += change * (line.percentage or 0.0) / 100.0
        return total

    def _get_mapping_payables_amount(self, row_key, company=None):
        """Sum residual amounts of unpaid/partial bills booked against the row's
        mapped accounts that were placed on behalf of this company (directly, or
        via a drop-ship sale to the related company), weighted by each line's
        percentage. Falls back to the mapping's manual amount when no account
        lines are configured."""
        company = company or self.company_id
        if not company:
            return 0.0

        mapping = self._get_mapping(row_key, company)
        if not mapping:
            return 0.0
        if not mapping.line_ids:
            return mapping.amount or 0.0

        date_from, date_to = self._get_date_range()
        account_ids = mapping.line_ids.account_id.ids
        amls = self.env['account.move.line'].sudo().search([
            ('account_id', 'in', account_ids),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('parent_state', '=', 'posted'),
        ])
        amls_by_account = defaultdict(lambda: self.env['account.move.line'])
        for aml in amls:
            amls_by_account[aml.account_id.id] |= aml

        company_partner = company.partner_id
        related_partner = company.related_company_id.partner_id if company.related_company_id else False
        Poline = self.env['purchase.order.line']
        has_sale_line = 'sale_line_id' in Poline._fields

        total = 0.0
        for line in mapping.line_ids:
            account_amls = amls_by_account.get(line.account_id.id)
            if not account_amls:
                continue
            bills = account_amls.mapped('move_id').filtered(
                lambda m: m.move_type == 'in_invoice'
                and m.state == 'posted'
                and m.payment_state in ('not_paid', 'partial')
            )
            line_total = 0.0
            for bill in bills:
                po_lines = bill.invoice_line_ids.mapped('purchase_line_id').filtered(lambda pl: pl)
                orders = po_lines.mapped('order_id')
                if not orders:
                    continue
                matched = False
                for po in orders:
                    if po.dest_address_id and po.dest_address_id == company_partner:
                        matched = True
                        break
                    if has_sale_line:
                        for so in po.order_line.mapped('sale_line_id.order_id').filtered(lambda s: s):
                            if related_partner and so.partner_id == related_partner:
                                matched = True
                                break
                            if not related_partner and so.partner_id == company_partner:
                                matched = True
                                break
                    if matched:
                        break
                if matched:
                    line_total += bill.amount_residual
            total += line_total * (line.percentage or 0.0) / 100.0
        return total

    def _get_net_profit(self):
        """Get net profit from standard P&L report using exact same method as standard report"""
        date_from, date_to = self._get_date_range()
        if not self.company_id:
            return 0.0

        # Get the standard P&L report
        pl_report = self.env.ref('account_reports.profit_and_loss').sudo().with_company(self.company_id).with_context(
            allowed_company_ids=[self.company_id.id]
        )

        # Create previous_options exactly like the standard report expects
        previous_options = {
            'date': {
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d'),
                'mode': 'range'
            }
        }

        previous_options['companies'] = [{'id': self.company_id.id, 'name': self.company_id.name}]

        # Get options using the standard method - this will handle all the complex logic
        pl_options = pl_report.get_options(previous_options)

        # Get the lines from P&L report
        lines = pl_report._get_lines(pl_options)

        # Find the Net Profit line - it should be the first line in P&L report
        if lines and lines[0].get('columns'):
            return lines[0]['columns'][0].get('no_format', 0.0)

        return 0.0

    def _calculate_threshold(self, data):
        """Calculate the Financial Security Threshold"""
        cash_flow = (
                - data['taxes'] +
                data['depreciation'] -
                data['capital_investments'] +
                data['change_payables_receivable'] +
                data['change_inventory'] -
                data['debt_retirement'] -
                data['investor_return_total'] -
                data['savings']
        )
        return cash_flow

    def _get_period_text(self):
        """Get human readable period text"""
        if self.duration == 'year':
            return f'Year {self.year}'
        elif self.duration == 'quarter':
            return f'{self.quarter} {self.year}'
        elif self.duration == 'month':
            month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December']
            return f'{month_names[int(self.month)]} {self.year}'
        return ''

    def _download_excel(self, data):
        """Generate and download Excel report"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Threshold Report')

        # Professional Header Formats
        main_title_format = workbook.add_format({
            'bold': True, 'font_size': 20, 'align': 'center', 'valign': 'vcenter',
            'font_color': '#FFFFFF', 'bg_color': '#1F4E79',
            'border': 2, 'border_color': '#0F2E4F'
        })

        subtitle_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter',
            'font_color': '#1F4E79', 'bg_color': '#F8F9FA',
            'border': 1, 'border_color': '#DEE2E6'
        })

        company_header_format = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'left',
            'font_color': '#495057', 'bg_color': '#E9ECEF',
            'border': 1, 'border_color': '#CED4DA'
        })

        period_header_format = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'right',
            'font_color': '#495057', 'bg_color': '#E9ECEF',
            'border': 1, 'border_color': '#CED4DA'
        })

        divider_format = workbook.add_format({
            'bg_color': '#6C757D', 'border': 0
        })

        header_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'left',
            'font_color': '#2E5984', 'bg_color': '#E8F1FF',
            'border': 1, 'border_color': '#B8D4F0'
        })

        label_format = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'left',
            'border': 1, 'border_color': '#D0D0D0'
        })

        value_format = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': '#,##0.00_);(#,##0.00)',
            'border': 1, 'border_color': '#D0D0D0'
        })

        red_value_format = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': '#,##0.00_);(#,##0.00)',
            'border': 1, 'border_color': '#D0D0D0',
            'font_color': '#C0392B'
        })

        # Total label format with larger font
        total_label_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'left',
            'border': 2, 'border_color': '#D35400',
            'font_color': '#D35400'
        })

        threshold_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'right', 'num_format': '#,##0.00_);(#,##0.00)',
            'font_color': '#FFFFFF', 'bg_color': '#E67E22',
            'border': 2, 'border_color': '#D35400'
        })

        info_format = workbook.add_format({
            'font_size': 9, 'align': 'left', 'italic': True,
            'font_color': '#666666'
        })

        # Professional Header Section
        # Main Title
        worksheet.set_row(1, 35)  # Set row height
        worksheet.merge_range(1, 0, 1, 1, 'FINANCIAL SECURITY THRESHOLD REPORT', main_title_format)

        # Subtitle
        worksheet.set_row(2, 25)
        worksheet.merge_range(2, 0, 2, 1, 'Cash Flow Analysis & Financial Planning', subtitle_format)

        # Company and Period Information Header
        worksheet.set_row(4, 20)
        period_text = self._get_period_text()
        company_text = ', '.join(self.company_id.mapped('name')) if self.company_id else 'All Companies'

        worksheet.write(4, 0, f'Company: {company_text}', company_header_format)
        worksheet.write(4, 1, f'Period: {period_text}', period_header_format)

        # Date Range and Generation Info
        worksheet.set_row(5, 18)
        worksheet.write(5, 0, f'Date Range: {data["date_from"]} to {data["date_to"]}', info_format)
        worksheet.write(5, 1, f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}', info_format)

        # Decorative divider
        worksheet.set_row(6, 3)
        worksheet.merge_range(6, 0, 6, 1, '', divider_format)

        # Data rows
        row = 8

        # Cash Flow Analysis Header
        worksheet.merge_range(row, 0, row, 1, 'CASH FLOW ANALYSIS', header_format)
        row += 2

        # Data items with formatting (excluding Change in A/R and Change in A/P)
        items = [
            ('Salary', data['salary'], value_format),
            ('Net Profit', data['pbt'], value_format),
            ('Taxes', -data['taxes'], red_value_format),
            ('Add back Depreciation', data['depreciation'], value_format),
            ('Capital Investments', -data['capital_investments'], red_value_format),
            ('Net Change in A/R and A/P', data['change_payables_receivable'], value_format),
            ('Change in Inventory', -data['change_inventory'], value_format),
            ('Debt Retirement - Principal Only', -data['debt_retirement'], red_value_format),
            ('Investor Return (Equity or Dividend)', -data['investor_return_total'], red_value_format),
            ('Savings', -data['savings'], red_value_format),
        ]

        for label, value, format_style in items:
            worksheet.write(row, 0, label, label_format)
            worksheet.write(row, 1, value, format_style)
            row += 1

        # Final Result with larger fonts
        row += 1
        worksheet.set_row(row, 25)  # Increase row height for total
        worksheet.write(row, 0, 'Financial Security Threshold', total_label_format)
        worksheet.write(row, 1, data['financial_threshold'], threshold_format)

        # Column widths - increased for wider header
        worksheet.set_column('A:A', 55)  # Increased from 45 to 55
        worksheet.set_column('B:B', 25)  # Increased from 20 to 25

        # Footer
        worksheet.write(row + 3, 0, 'Generated by Odoo Threshold Report Module', info_format)

        workbook.close()
        output.seek(0)

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Threshold_Report_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
