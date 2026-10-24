# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    x_preferred = fields.Boolean(
        string='Preferred Vendor',
        help='Use this vendor line as the cost for Sync Vendor Prices, whatever the order the list is shown in for '
             'each user. Without a preferred line the first line by sequence is used.',
    )
