from odoo import fields, models


class ResCompanyExt(models.Model):
    _inherit = 'res.company'

    related_company_id = fields.Many2one('res.company', string='Related Company')
    required_threshold = fields.Boolean(string='Required Threshold Report')
