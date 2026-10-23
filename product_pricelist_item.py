# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

COST_SOURCES = [
    ('vendor_pricelist', 'Vendor price list'),
    ('vendor_bill', 'Vendor bill'),
    ('average_cost', 'Average cost'),
    ('manual', 'Entered manually'),
]


def price_from_margin(cost, margin):
    """Gross margin: price = cost / (1 - margin)."""
    return cost / (1.0 - margin / 100.0)


def margin_from_price(cost, price):
    return (price - cost) / price * 100.0 if price else 0.0


def cost_from_price(price, margin):
    return price * (1.0 - margin / 100.0)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    vendor_cost = fields.Float(
        string='Vendor Cost',
        digits='Product Price',
        help='Cost used for the price: vendor price list, then latest vendor bill, then average cost '
             '(filled by Sync Vendor Prices) - or entered manually.',
    )
    # technical name kept for existing data; the value is a GROSS MARGIN since 17.0.1.1.0
    percentage_extra = fields.Float(
        string='Gross Margin (%)',
        digits=(16, 2),
        help='Gross margin on the vendor cost: price = cost / (1 - margin). 50% doubles the cost.',
    )
    cost_source = fields.Selection(COST_SOURCES, string='Cost Source', readonly=True,
                                   help='Where Sync Vendor Prices took the vendor cost from.')

    @api.constrains('percentage_extra')
    def _check_percentage_extra(self):
        for item in self:
            if item.percentage_extra >= 100.0:
                raise ValidationError(_("A gross margin must be below 100%."))

    # ---------------- on-screen calculations ----------------
    @api.onchange('pricelist_id')
    def _onchange_pricelist_id_set_percentage(self):
        if self.pricelist_id and self.pricelist_id.tier_id and self.pricelist_id.tier_id.percentage and not self.percentage_extra:
            self.percentage_extra = self.pricelist_id.tier_id.percentage

    @api.onchange('vendor_cost')
    def _onchange_vendor_cost(self):
        self.cost_source = 'manual' if self.vendor_cost else False
        if not self.vendor_cost:
            return
        if self.percentage_extra and self.percentage_extra < 100.0:
            self.fixed_price = price_from_margin(self.vendor_cost, self.percentage_extra)
        elif self.fixed_price:
            self.percentage_extra = margin_from_price(self.vendor_cost, self.fixed_price)

    @api.onchange('percentage_extra')
    def _onchange_percentage_extra(self):
        if self.percentage_extra >= 100.0:
            return {'warning': {'title': _("Gross margin"), 'message': _("A gross margin must be below 100%.")}}
        if self.vendor_cost:
            self.fixed_price = price_from_margin(self.vendor_cost, self.percentage_extra)
        elif self.fixed_price:
            self.vendor_cost = cost_from_price(self.fixed_price, self.percentage_extra)

    @api.onchange('fixed_price')
    def _onchange_fixed_price(self):
        if self.vendor_cost:
            self.percentage_extra = margin_from_price(self.vendor_cost, self.fixed_price)
        elif self.percentage_extra and self.percentage_extra < 100.0:
            self.vendor_cost = cost_from_price(self.fixed_price, self.percentage_extra)

    # ---------------- stored consistency ----------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            pricelist_id = vals.get('pricelist_id')
            if pricelist_id and 'percentage_extra' not in vals:
                pricelist = self.env['product.pricelist'].browse(pricelist_id)
                if pricelist.tier_id and pricelist.tier_id.percentage:
                    vals['percentage_extra'] = pricelist.tier_id.percentage
            cost = vals.get('vendor_cost') or 0.0
            margin = vals.get('percentage_extra') or 0.0
            price = vals.get('fixed_price') or 0.0
            if cost and margin and not price and margin < 100.0:
                vals['fixed_price'] = price_from_margin(cost, margin)
            elif price and margin and not cost and margin < 100.0:
                vals['vendor_cost'] = cost_from_price(price, margin)
            elif cost and price and not vals.get('percentage_extra'):
                vals['percentage_extra'] = margin_from_price(cost, price)
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if self.env.context.get('liber_no_recompute'):
            return res
        if {'vendor_cost', 'percentage_extra', 'fixed_price'} & set(vals):
            for item in self:
                fix = {}
                if 'fixed_price' not in vals and ('vendor_cost' in vals or 'percentage_extra' in vals):
                    if item.vendor_cost and item.percentage_extra < 100.0:
                        fix['fixed_price'] = price_from_margin(item.vendor_cost, item.percentage_extra)
                elif 'fixed_price' in vals and 'vendor_cost' not in vals and item.percentage_extra and item.percentage_extra < 100.0:
                    fix['vendor_cost'] = cost_from_price(item.fixed_price, item.percentage_extra)
                if fix:
                    super(ProductPricelistItem, item.with_context(liber_no_recompute=True)).write(fix)
        return res
