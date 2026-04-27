import base64
import io
from datetime import datetime, date

import xlsxwriter
from dateutil.relativedelta import relativedelta
from odoo import models, fields
from odoo.exceptions import UserError


class ThresholdReportWizard(models.TransientModel):
    _name = 'threshold.report.wizard'
    _description = 'Threshold Report Wizard'

    company_ids = fields.Many2many(
        'res.company',
        'threshold_report_wizard_company_rel',
        'wizard_id',
        'company_id',
        string='Companies',
    )
    purchase_company_ids = fields.Many2many(
        'res.company',
        'threshold_report_wizard_purchase_company_rel',
        'wizard_id',
        'company_id',
        string='Purchase Companies',
    )
    capital_investments = fields.Float(string='Capital Investments', default=100000.0)
    savings = fields.Float(string='Savings', default=50000.0)
    investor_return = fields.Float(string='Investor Return', default=0.0)
    tax = fields.Float(string='Tax', default=0.0)
    start_date = fields.Date(string='Start Date', required=True, default=lambda self: date(datetime.now().year, 1, 1))
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.today)
    purchase_percentage = fields.Float(string='Purchase Percentage (%)', default=0.0)

    def _get_date_range(self):
        """Return selected custom date range."""
        return self.start_date, self.end_date

    def action_download_excel(self):
        if not self.company_ids:
            raise UserError('Please select at least one company.')
        if not self.purchase_company_ids:
            raise UserError('Please select at least one purchase company.')
        if not self.start_date or not self.end_date:
            raise UserError('Please set a valid start and end date.')
        if self.start_date > self.end_date:
            raise UserError('Start date cannot be after end date.')
        if self.purchase_percentage < 0:
            raise UserError('Purchase percentage cannot be negative.')

        data = self._get_threshold_data()
        return self._download_excel(data)

    def _get_selected_company_ids(self):
        return self.company_ids.ids

    def _get_report_companies(self):
        return [{'id': company.id, 'name': company.name} for company in self.company_ids]

    def _get_purchase_company_ids(self):
        return self.purchase_company_ids.ids

    def _get_threshold_data(self):
        """Calculate all threshold report values"""

        # Get date range based on selection
        date_from, date_to = self._get_date_range()

        data = {
            'date_from': date_from,
            'date_to': date_to
        }

        # Get salary (account code 240100)
        data['salary'] = self._get_account_balance('240100')

        data['taxes'] = self.tax or 0

        # Get net profit and calculate PBT
        net_profit = self._get_net_profit()
        data['pbt'] = net_profit

        data['depreciation'] = self._get_account_balance('06.2.102')

        # Capital investments from wizard
        data['capital_investments'] = self.capital_investments

        # Change in A/R (using Trial Balance approach)
        data['change_ar'] = self._get_balance_change_from_trial_balance('asset_receivable')

        data['change_payables'] = self._get_payables_threshold_amount('02.1.101')

        # Change Net Change in A/R and A/P
        data['change_payables_receivable'] = data['change_ar'] + data['change_payables']

        # Change in Inventory (using Trial Balance approach)
        data['change_inventory'] = self._get_balance_change_from_trial_balance('asset_current')

        # Get depreciation with company-specific account codes
        depreciation_accounts = ['02.2.202', '02.1.402', '02.2.201']
        data['debt_retirement'] = self._get_account_balance_related(depreciation_accounts)

        # Investor Return (wizard value + account 03.0.004)
        account_investor_return = self._get_account_balance('03.0.004')
        data['investor_return_total'] = self.investor_return + account_investor_return

        # Savings from wizard
        data['savings'] = self.savings

        # Purchases in period based on selected percentage
        data['purchase_total'] = self._get_total_purchase_amount()
        data['purchase_percentage'] = self.purchase_percentage
        data['purchase_percentage_amount'] = self._get_purchase_percentage_amount(data['purchase_total'])
        data['purchase_companies_text'] = ', '.join(self.purchase_company_ids.mapped('name'))

        # Calculate Financial Security Threshold
        data['financial_threshold'] = self._calculate_threshold(data)

        return data

    def _get_payables_threshold_amount(self, account_code='02.1.101'):
        self.ensure_one()
        company_ids = self._get_selected_company_ids()
        if not company_ids:
            return 0.0
        date_from, date_to = self._get_date_range()
        Account = self.env['account.account'].sudo()
        accounts = Account.search([('code', '=', account_code), ('company_id', 'in', company_ids)])
        if not accounts:
            return 0.0
        MoveLine = self.env['account.move.line'].sudo()
        amls = MoveLine.search([
            ('account_id', 'in', accounts.ids),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('parent_state', '=', 'posted'),
        ])
        bills = amls.mapped('move_id').filtered(
            lambda m: m.move_type == 'in_invoice'
            and m.state == 'posted'
            and m.payment_state in ('not_paid', 'partial')
            and m.company_id.id in company_ids
        )
        Poline = self.env['purchase.order.line']
        has_sale_line = 'sale_line_id' in Poline._fields
        company_partners = self.company_ids.mapped('partner_id')
        related_partners = self.company_ids.mapped('related_company_id.partner_id')
        valid_partners = company_partners | related_partners
        total = 0.0
        for bill in bills:
            po_lines = bill.invoice_line_ids.mapped('purchase_line_id').filtered(lambda pl: pl)
            orders = po_lines.mapped('order_id')
            if not orders:
                continue
            matched = False
            for po in orders:
                if po.dest_address_id and po.dest_address_id in valid_partners:
                    matched = True
                    break
                if has_sale_line:
                    for so in po.order_line.mapped('sale_line_id.order_id').filtered(lambda s: s):
                        if so.partner_id in valid_partners:
                            matched = True
                            break
                if matched:
                    break
            if matched:
                total += bill.amount_residual
        return total

    def _get_total_purchase_amount(self):
        date_from, date_to = self._get_date_range()
        company_ids = self._get_purchase_company_ids()
        if not company_ids:
            return 0.0

        purchase_orders = self.env['purchase.order'].sudo().search([
            ('company_id', 'in', company_ids),
            ('state', 'in', ['purchase', 'done']),
            ('date_approve', '>=', datetime.combine(date_from, datetime.min.time())),
            ('date_approve', '<=', datetime.combine(date_to, datetime.max.time())),
        ])
        return sum(purchase_orders.mapped('amount_total'))

    def _get_purchase_percentage_amount(self, total_purchase):
        return total_purchase * ((self.purchase_percentage or 0.0) / 100.0)

    def _get_account_balance(self, account_code, date_from=None, date_to=None):
        """Get account balance for specified code and period"""
        if not date_from or not date_to:
            date_from, date_to = self._get_date_range()
        company_ids = self._get_selected_company_ids()
        if not company_ids:
            return 0.0

        domain = [('code', '=', account_code), ('company_id', 'in', company_ids)]

        accounts = self.env['account.account'].sudo().search(domain)

        if not accounts:
            return 0.0

        domain = [
            ('account_id', 'in', accounts.ids),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('move_id.state', '=', 'posted')
        ]

        moves = self.env['account.move.line'].sudo().search(domain)
        return sum(moves.mapped('balance'))

    def _get_account_balance_related(self, account_codes, date_from=None, date_to=None):
        """Get account balance for specified codes and period"""
        if not date_from or not date_to:
            date_from, date_to = self._get_date_range()

        if isinstance(account_codes, str):
            account_codes = [account_codes]

        company_ids = self._get_selected_company_ids()
        if not company_ids:
            return 0.0

        total_balance = 0.0
        related_accounts = ['02.2.201', '01.1.110', '01.1.105', '01.1.104']
        liber_balance = 0.0
        for related_account_code in related_accounts:
            related_company_balance = self._get_related_balance(related_account_code, date_from, date_to)
            liber_balance += related_company_balance
        total_balance += liber_balance * 0.5

        for account_code in account_codes:
            company_balance = self._get_single_account_balance(account_code, date_from, date_to)
            total_balance += company_balance

        return total_balance

    def _get_single_account_balance(self, account_code, date_from, date_to):
        """Get movement in date range for selected companies and account code."""
        company_ids = self._get_selected_company_ids()
        if not company_ids:
            return 0.0

        accounts = self.env['account.account'].sudo().search([
            ('code', '=', account_code),
            ('company_id', 'in', company_ids),
        ])
        if not accounts:
            return 0.0

        move_lines = self.env['account.move.line'].sudo().search([
            ('account_id', 'in', accounts.ids),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('move_id.state', '=', 'posted'),
        ])
        return sum(move_lines.mapped('balance'))

    def _get_related_balance(self, account_code, date_from, date_to):
        """Get balance for a single related company account code from Trial Balance report."""
        related_companies = self.company_ids.mapped('related_company_id').filtered(lambda c: c)
        if not related_companies:
            return 0.0

        related_company_ids = related_companies.ids
        trial_balance_report = self.env.ref('account_reports.trial_balance_report').sudo().with_company(related_companies[0]).with_context(
            allowed_company_ids=related_company_ids
        )
        previous_options = {
            'date': {
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d'),
                'mode': 'range'
            },
            'companies': [{'id': company.id, 'name': company.name} for company in related_companies],
        }
        report_options = trial_balance_report.get_options(previous_options)
        lines = trial_balance_report._get_lines(report_options)

        for line in lines:
            name = (line.get('name') or '').strip()
            code = (line.get('code') or '').strip()
            if code == account_code or (name and name.split(' ')[0] == account_code):
                columns = line.get('columns') or []
                numeric_columns = [col.get('no_format') for col in columns if isinstance(col.get('no_format'), (int, float))]
                if len(numeric_columns) >= 2:
                    return numeric_columns[-2] - numeric_columns[-1]
                if numeric_columns:
                    return numeric_columns[-1]
                return 0.0
        return 0.0

    def _get_net_profit(self):
        """Get net profit from standard P&L report using exact same method as standard report"""
        date_from, date_to = self._get_date_range()
        company_ids = self._get_selected_company_ids()
        if not company_ids:
            return 0.0

        primary_company = self.company_ids[0]
        # Get the standard P&L report
        pl_report = self.env.ref('account_reports.profit_and_loss').sudo().with_company(primary_company).with_context(
            allowed_company_ids=company_ids
        )

        # Create previous_options exactly like the standard report expects
        previous_options = {
            'date': {
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d'),
                'mode': 'range'
            }
        }

        previous_options['companies'] = self._get_report_companies()

        # Get options using the standard method - this will handle all the complex logic
        pl_options = pl_report.get_options(previous_options)

        # Get the lines from P&L report
        lines = pl_report._get_lines(pl_options)

        # Find the Net Profit line - it should be the first line in P&L report
        if lines and lines[0].get('columns'):
            return lines[0]['columns'][0].get('no_format', 0.0)

        return 0.0

    def _get_balance_change_from_trial_balance(self, account_type):
        """Get balance change by calculating opening and closing balances directly"""
        date_from, date_to = self._get_date_range()

        # Get opening balance (as of day before period start)
        opening_date = date_from - relativedelta(days=1)
        opening_balance = self._get_balance_as_of_date(account_type, opening_date)

        # Get closing balance (as of period end)
        closing_balance = self._get_balance_as_of_date(account_type, date_to)

        # Return the change (closing - opening)
        return closing_balance - opening_balance

    def _get_balance_as_of_date(self, account_type, as_of_date):
        """Get total balance for account type as of specific date"""
        company_ids = self._get_selected_company_ids()
        if not company_ids:
            return 0.0
        # Get accounts of the specified type
        domain = [('account_type', '=', account_type), ('company_id', 'in', company_ids)]

        accounts = self.env['account.account'].sudo().search(domain)

        if not accounts:
            return 0.0
        if accounts and account_type == 'asset_current':
            accounts = accounts.filtered(lambda a: a.code in ['101110', '01.1.401'])

        # Get all move lines up to the specified date
        move_domain = [
            ('account_id', 'in', accounts.ids),
            ('date', '<=', as_of_date),
            ('move_id.state', '=', 'posted')
        ]

        moves = self.env['account.move.line'].sudo().search(move_domain)
        return sum(moves.mapped('balance'))

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
                data['savings'] -
                data['purchase_percentage_amount']
        )
        return cash_flow

    def _get_period_text(self):
        """Get human readable period text"""
        if self.start_date and self.end_date:
            return f'{self.start_date} to {self.end_date}'
        return 'Custom Period'

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

        percentage_format = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': '0.00%',
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
        company_text = ', '.join(self.company_ids.mapped('name')) if self.company_ids else 'All Companies'

        worksheet.write(4, 0, f'Company: {company_text}', company_header_format)
        worksheet.write(4, 1, f'Period: {period_text}', period_header_format)

        # Date Range and Generation Info
        worksheet.set_row(5, 18)
        worksheet.write(5, 0, f'Date Range: {data["date_from"]} to {data["date_to"]}', info_format)
        worksheet.write(5, 1, f'Generated: {datetime.now().strftime("%B %d, %Y at %H:%M")}', info_format)
        worksheet.write(6, 0, f'Purchase Companies: {data["purchase_companies_text"] or "None"}', info_format)

        # Decorative divider
        worksheet.set_row(7, 3)
        worksheet.merge_range(7, 0, 7, 1, '', divider_format)

        # Data rows
        row = 9

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
            ('Purchase %', (data['purchase_percentage'] or 0.0) / 100.0, percentage_format),
            ('Purchase Amount (from %)', -data['purchase_percentage_amount'], red_value_format),
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
