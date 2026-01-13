from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io
import xlsxwriter
import base64


class ThresholdReportWizard(models.TransientModel):
    _name = 'threshold.report.wizard'
    _description = 'Threshold Report Wizard'

    company_ids = fields.Many2many('res.company', string='Companies')
    capital_investments = fields.Float(string='Capital Investments', default=100000.0)
    savings = fields.Float(string='Savings', default=50000.0)
    investor_return = fields.Float(string='Investor Return', default=0.0)
    
    duration = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year')
    ], string='Duration', required=True, default='year')
    
    year = fields.Selection(selection='_get_year_selection', string='Year', default=lambda self: str(datetime.now().year))
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
            return date(year, start_month, 1), date(year, end_month, 1) + relativedelta(months=1) - relativedelta(days=1)
        elif self.duration == 'month':
            year = int(self.year) if self.year else datetime.now().year
            month = int(self.month)
            start_date = date(year, month, 1)
            end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
            return start_date, end_date

    def action_download_excel(self):
        # Validate required fields based on duration
        if self.duration == 'year' and not self.year:
            raise UserError('Please select a year.')
        elif self.duration == 'quarter' and (not self.year or not self.quarter):
            raise UserError('Please select a year and quarter.')
        elif self.duration == 'month' and (not self.year or not self.month):
            raise UserError('Please select a year and month.')
        
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
        
        # Get salary (account code 240100)
        data['salary'] = self._get_account_balance('240100')
        
        # Get tax (account code 240400)
        tax_amount = self._get_account_balance('240400')
        data['taxes'] = tax_amount
        
        # Get net profit and calculate PBT
        net_profit = self._get_net_profit()
        data['pbt'] = net_profit + tax_amount
        
        # Get depreciation (account code 06.2.102)
        data['depreciation'] = self._get_account_balance('06.2.102')
        
        # Capital investments from wizard
        data['capital_investments'] = self.capital_investments
        
        # Change in A/R (using Trial Balance approach)
        data['change_ar'] = self._get_balance_change_from_trial_balance('asset_receivable')
        
        # Change in A/P (using Trial Balance approach)
        data['change_payables'] = self._get_balance_change_from_trial_balance('liability_payable')
        
        # Change in Inventory (using Trial Balance approach)
        data['change_inventory'] = self._get_balance_change_from_trial_balance('asset_current')
        
        # Debt Retirement (account code 02.2.202)
        data['debt_retirement'] = self._get_account_balance('02.2.202')
        
        # Investor Return (wizard value + account 03.0.004)
        account_investor_return = self._get_account_balance('03.0.004')
        data['investor_return_total'] = self.investor_return + account_investor_return
        
        # Savings from wizard
        data['savings'] = self.savings
        
        # Calculate Financial Security Threshold
        data['financial_threshold'] = self._calculate_threshold(data)
        
        return data

    def _get_account_balance(self, account_code, date_from=None, date_to=None):
        """Get account balance for specified code and period"""
        if not date_from or not date_to:
            date_from, date_to = self._get_date_range()
        
        domain = [('code', '=', account_code)]
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        else:
            # Use all companies if none selected
            all_companies = self.env['res.company'].search([])
            domain.append(('company_id', 'in', all_companies.ids))
            
        accounts = self.env['account.account'].search(domain)
        
        if not accounts:
            return 0.0
        
        domain = [
            ('account_id', 'in', accounts.ids),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('move_id.state', '=', 'posted')
        ]
        
        moves = self.env['account.move.line'].search(domain)
        return sum(moves.mapped('balance'))

    def _get_net_profit(self):
        """Get net profit from standard P&L report using exact same method as standard report"""
        date_from, date_to = self._get_date_range()
        
        # Get the standard P&L report
        pl_report = self.env.ref('account_reports.profit_and_loss')
        
        # Create previous_options exactly like the standard report expects
        previous_options = {
            'date': {
                'date_from': date_from.strftime('%Y-%m-%d'),
                'date_to': date_to.strftime('%Y-%m-%d'),
                'mode': 'range'
            }
        }
        
        # If companies are selected, add them to previous_options
        if self.company_ids:
            previous_options['companies'] = [{'id': company.id, 'name': company.name} for company in self.company_ids]
        else:
            # Use all companies if none selected
            all_companies = self.env['res.company'].search([])
            previous_options['companies'] = [{'id': company.id, 'name': company.name} for company in all_companies]
        
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
        # Get accounts of the specified type
        domain = [('account_type', '=', account_type)]
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        else:
            # Use all companies if none selected
            all_companies = self.env['res.company'].search([])
            domain.append(('company_id', 'in', all_companies.ids))

        accounts = self.env['account.account'].search(domain)

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
        
        moves = self.env['account.move.line'].search(move_domain)
        return sum(moves.mapped('balance'))
    


    def _calculate_threshold(self, data):
        """Calculate the Financial Security Threshold"""
        cash_flow = (
            data['salary'] + 
            data['pbt'] +
            data['taxes'] + 
            data['depreciation'] - 
            data['capital_investments'] - 
            data['change_ar'] + 
            data['change_payables'] - 
            data['change_inventory'] - 
            data['debt_retirement'] - 
            data['investor_return_total'] + 
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
        company_text = ', '.join(self.company_ids.mapped('name')) if self.company_ids else 'All Companies'
        
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
        
        # Data items with formatting
        items = [
            ('Salary', data['salary'], value_format),
            ('PBT (Profit Before Tax)', data['pbt'], value_format),
            ('Taxes', -data['taxes'], red_value_format),
            ('Add back Depreciation', data['depreciation'], value_format),
            ('Capital Investments', -data['capital_investments'], red_value_format),
            ('Change in A/R', -data['change_ar'], red_value_format),
            ('Change in A/P', data['change_payables'], value_format),
            ('Change in Inventory', -data['change_inventory'], value_format),
            ('Debt Retirement - Principal Only', -data['debt_retirement'], red_value_format),
            ('Investor Return (Equity or Dividend)', -data['investor_return_total'], red_value_format),
            ('Savings', data['savings'], value_format),
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