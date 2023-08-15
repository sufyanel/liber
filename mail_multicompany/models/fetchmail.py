from odoo import fields, models, api


class FetchMail(models.Model):
    _inherit = 'fetchmail.server'

    company_id = fields.Many2one("res.company", "Company")
