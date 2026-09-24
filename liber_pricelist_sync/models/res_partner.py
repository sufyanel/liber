# -*- coding: utf-8 -*-

from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tier_id = fields.Many2one(
        'pricelist.tier',
        string='Tier',
        help='Select tier assigned to this contact.'
    )
