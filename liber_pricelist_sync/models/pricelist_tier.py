# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PricelistTier(models.Model):
    _name = 'pricelist.tier'
    _description = 'Pricelist Tier'
    _order = 'sequence, name'

    name = fields.Char(string='Tier Name', required=True)
    percentage = fields.Float(
        string='Gross Margin (%)',
        digits=(16, 2),
        help='Default gross margin for pricelists assigned to this tier: price = cost / (1 - margin). '
             '50% gross margin doubles the cost.',
    )
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')

    @api.constrains('percentage')
    def _check_percentage(self):
        for tier in self:
            if tier.percentage >= 100.0:
                raise ValidationError(_("A gross margin must be below 100%% (tier %s).") % tier.name)
