# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    vendor_cost = fields.Float(
        string='Vendor Cost',
        digits='Product Price',
        help='Vendor cost fetched from PO or set manually.'
    )
    percentage_extra = fields.Float(
        string='Percentage Extra (%)',
        digits=(16, 2),
        help='Percentage extra markup added to vendor cost.'
    )

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id_set_percentage(self):
        if self.pricelist_id and self.pricelist_id.tier_id and self.pricelist_id.tier_id.percentage and not self.percentage_extra:
            self.percentage_extra = self.pricelist_id.tier_id.percentage

    @api.onchange('vendor_cost')
    def _onchange_vendor_cost(self):
        if self.vendor_cost:
            if self.percentage_extra:
                self.fixed_price = self.vendor_cost * (1.0 + (self.percentage_extra / 100.0))
            elif self.fixed_price and self.vendor_cost != 0:
                self.percentage_extra = ((self.fixed_price - self.vendor_cost) / self.vendor_cost) * 100.0

    @api.onchange('percentage_extra')
    def _onchange_percentage_extra(self):
        if self.vendor_cost:
            self.fixed_price = self.vendor_cost * (1.0 + (self.percentage_extra / 100.0))
        elif self.fixed_price and (1.0 + (self.percentage_extra / 100.0)) != 0:
            self.vendor_cost = self.fixed_price / (1.0 + (self.percentage_extra / 100.0))

    @api.onchange('fixed_price')
    def _onchange_fixed_price(self):
        if self.percentage_extra and (1.0 + (self.percentage_extra / 100.0)) != 0:
            self.vendor_cost = self.fixed_price / (1.0 + (self.percentage_extra / 100.0))
        elif self.vendor_cost and self.vendor_cost != 0:
            self.percentage_extra = ((self.fixed_price - self.vendor_cost) / self.vendor_cost) * 100.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            pricelist_id = vals.get('pricelist_id')
            if pricelist_id and 'percentage_extra' not in vals:
                pricelist = self.env['product.pricelist'].browse(pricelist_id)
                if pricelist.tier_id and pricelist.tier_id.percentage:
                    vals['percentage_extra'] = pricelist.tier_id.percentage

            vendor_cost = vals.get('vendor_cost', 0.0)
            percentage_extra = vals.get('percentage_extra', 0.0)
            fixed_price = vals.get('fixed_price', 0.0)

            if vendor_cost and percentage_extra and not vals.get('fixed_price'):
                vals['fixed_price'] = vendor_cost * (1.0 + (percentage_extra / 100.0))
            elif fixed_price and percentage_extra and not vals.get('vendor_cost'):
                if (1.0 + (percentage_extra / 100.0)) != 0:
                    vals['vendor_cost'] = fixed_price / (1.0 + (percentage_extra / 100.0))
            elif vendor_cost and fixed_price and not vals.get('percentage_extra') and vendor_cost != 0:
                vals['percentage_extra'] = ((fixed_price - vendor_cost) / vendor_cost) * 100.0

        return super(ProductPricelistItem, self).create(vals_list)

    def write(self, vals):
        res = super(ProductPricelistItem, self).write(vals)
        if 'vendor_cost' in vals or 'percentage_extra' in vals or 'fixed_price' in vals:
            for item in self:
                if 'vendor_cost' in vals and 'percentage_extra' in vals and 'fixed_price' not in vals:
                    new_fixed_price = item.vendor_cost * (1.0 + (item.percentage_extra / 100.0))
                    super(ProductPricelistItem, item).write({'fixed_price': new_fixed_price})
                elif 'vendor_cost' in vals and 'fixed_price' not in vals and item.percentage_extra:
                    new_fixed_price = item.vendor_cost * (1.0 + (item.percentage_extra / 100.0))
                    super(ProductPricelistItem, item).write({'fixed_price': new_fixed_price})
                elif 'percentage_extra' in vals and 'fixed_price' not in vals and item.vendor_cost:
                    new_fixed_price = item.vendor_cost * (1.0 + (item.percentage_extra / 100.0))
                    super(ProductPricelistItem, item).write({'fixed_price': new_fixed_price})
                elif 'fixed_price' in vals and 'vendor_cost' not in vals and item.percentage_extra:
                    if (1.0 + (item.percentage_extra / 100.0)) != 0:
                        new_vendor_cost = item.fixed_price / (1.0 + (item.percentage_extra / 100.0))
                        super(ProductPricelistItem, item).write({'vendor_cost': new_vendor_cost})
        return res
