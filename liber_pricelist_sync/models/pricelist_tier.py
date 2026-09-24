# -*- coding: utf-8 -*-

from odoo import models, fields

class PricelistTier(models.Model):
    _name = 'pricelist.tier'
    _description = 'Pricelist Tier'
    _order = 'sequence, name'

    name = fields.Char(string='Tier Name', required=True)
    percentage = fields.Float(
        string='Percentage Tier (%)',
        digits=(16, 2),
        help='Default percentage extra applied to pricelists assigned to this tier.'
    )
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description')
