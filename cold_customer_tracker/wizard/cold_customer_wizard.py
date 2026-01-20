from odoo import fields, models


class ColdCustomerWizard(models.TransientModel):
    _name = 'cold.customer.wizard'
    _description = 'Cold Customer Date Range Wizard'

    date_from = fields.Date(string='Date From', required=True)
    date_to = fields.Date(string='Date To', required=True)

    def action_show_cold_customers(self):
        return {
            'name': 'Cold Customers',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('is_cold_customer', '=', True)],
            'context': {
                'cold_date_from': self.date_from,
                'cold_date_to': self.date_to,
            }
        }
