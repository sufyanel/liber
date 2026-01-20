from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_cold_customer = fields.Boolean(
        string='Cold Customer',
        compute='_compute_is_cold_customer',
        search='_search_is_cold_customer',
        store=False
    )

    @api.depends_context('cold_date_from', 'cold_date_to')
    def _compute_is_cold_customer(self):
        date_from = self.env.context.get('cold_date_from')
        date_to = self.env.context.get('cold_date_to')
        
        for partner in self:
            partner.is_cold_customer = False
            if date_from and date_to:
                invoice_count = self.env['account.move'].search_count([
                    ('partner_id', '=', partner.id),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '=', 'posted'),
                    ('invoice_date', '>=', date_from),
                    ('invoice_date', '<=', date_to)
                ])
                partner.is_cold_customer = invoice_count == 0

    def _search_is_cold_customer(self, operator, value):
        date_from = self.env.context.get('cold_date_from')
        date_to = self.env.context.get('cold_date_to')
        
        if not date_from or not date_to:
            return [('id', '=', False)]
        
        invoices = self.env['account.move'].search([
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<=', date_to)
        ])
        
        partner_ids_with_invoices = invoices.mapped('partner_id').ids
        
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'not in', partner_ids_with_invoices)]
        else:
            return [('id', 'in', partner_ids_with_invoices)]
