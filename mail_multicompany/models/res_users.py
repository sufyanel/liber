from odoo import api, fields, models


class UsersModified(models.Model):
    _inherit = 'res.users'

    @api.model
    def set_current_company(self, company_id):
        user = self.env.user
        user.sudo().write({'company_id': company_id})
