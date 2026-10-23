# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class ResUsers(models.Model):
    _inherit = 'res.users'

    login_alias_ids = fields.One2many('res.users.login.alias', 'user_id', string='Alternative Logins',
                                      groups='base.group_system')

    @api.model
    def _get_login_domain(self, login):
        """Sign in with the main login or with one of the user's alternative logins (Dale, 23 Oct 2026).
        The password check, lockout and 2FA are Odoo's own and unchanged."""
        domain = super()._get_login_domain(login)
        key = (login or '').strip().lower()
        if key:
            alias = self.env['res.users.login.alias'].sudo().search([('name', '=', key)], limit=1)
            if alias:
                domain = expression.OR([domain, [('id', '=', alias.user_id.id)]])
        return domain

    @api.constrains('login')
    def _check_login_not_an_alias(self):
        Alias = self.env['res.users.login.alias'].sudo()
        for user in self:
            key = (user.login or '').strip().lower()
            alias = key and Alias.search([('name', '=', key), ('user_id', '!=', user.id)], limit=1)
            if alias:
                raise ValidationError(_('"%s" is already an alternative login of %s.') % (user.login, alias.user_id.name))
