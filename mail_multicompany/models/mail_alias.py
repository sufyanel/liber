import ast
import re

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import is_html_empty, remove_accents


class MailAlias(models.Model):
    _inherit = 'mail.alias'

    alias_domain = fields.Char('Alias domain', compute='_compute_alias_domain', store=True, readonly=False)

    @api.depends('alias_name')
    def _compute_alias_domain(self):
        for record in self:
            if record.alias_domain:
                pass
            else:
                record.alias_domain = self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain")


