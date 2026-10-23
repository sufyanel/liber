# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsersLoginAlias(models.Model):
    _name = 'res.users.login.alias'
    _description = 'Alternative Login'
    _order = 'name'

    name = fields.Char(string='Alternative Login', required=True,
                       help='Another address this user can sign in with, using the same password.')
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade', index=True)

    _sql_constraints = [('name_unique', 'unique(name)', 'This alternative login is already used.')]

    @api.model
    def _normalize(self, value):
        return (value or '').strip().lower()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = self._normalize(vals['name'])
        return super().create(vals_list)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = self._normalize(vals['name'])
        return super().write(vals)

    @api.constrains('name', 'user_id')
    def _check_not_another_users_login(self):
        Users = self.env['res.users'].sudo().with_context(active_test=False)
        for alias in self:
            if not alias.name:
                raise ValidationError(_('An alternative login cannot be empty.'))
            other = Users.search([('login', '=ilike', alias.name), ('id', '!=', alias.user_id.id)], limit=1)
            if other:
                raise ValidationError(_('"%s" is already the login of another user (%s).') % (alias.name, other.name))
            if alias.name == (alias.user_id.login or '').strip().lower():
                raise ValidationError(_('"%s" is already this user\'s main login.') % alias.name)
