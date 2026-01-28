from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_cold_customer = fields.Boolean(string='Cold Customer', default=False)

    @api.model
    def _cron_mark_cold_customers(self):
        Config = self.env['ir.config_parameter'].sudo()
        start_date = Config.get_param('cold_customer_start_date')
        end_date = Config.get_param('cold_customer_end_date')
        
        if not start_date or not end_date:
            return
        
        # Get all customers with invoices in the date range
        invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date)
        ])
        
        partners_with_invoices = invoices.mapped('partner_id')
        
        # Mark all customers as not cold first
        all_customers = self.search([('is_cold_customer', '=', True)])
        all_customers.write({'is_cold_customer': False})
        
        # Mark customers without invoices as cold
        cold_customers = self.search([
            ('id', 'not in', partners_with_invoices.ids),
            ('customer_rank', '>', 0)
        ])
        cold_customers.write({'is_cold_customer': True})
