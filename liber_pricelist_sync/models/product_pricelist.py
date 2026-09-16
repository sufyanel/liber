# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    tier_id = fields.Many2one(
        'pricelist.tier',
        string='Tier',
        help='Select tier assigned to this pricelist.'
    )

    @api.onchange('tier_id')
    def _onchange_tier_id_apply_percentage(self):
        if self.tier_id and self.tier_id.percentage:
            percentage = self.tier_id.percentage
            for item in self.item_ids:
                item.percentage_extra = percentage
                if item.vendor_cost:
                    item.fixed_price = item.vendor_cost * (1.0 + (percentage / 100.0))

    def write(self, vals):
        res = super(ProductPricelist, self).write(vals)
        if 'tier_id' in vals:
            for pricelist in self:
                if pricelist.tier_id and pricelist.tier_id.percentage:
                    percentage = pricelist.tier_id.percentage
                    for item in pricelist.item_ids:
                        new_vals = {'percentage_extra': percentage}
                        if item.vendor_cost:
                            new_vals['fixed_price'] = item.vendor_cost * (1.0 + (percentage / 100.0))
                        item.write(new_vals)
        return res

    def action_sync_vendor_prices(self):
        self.ensure_one()

        # Collect existing pricelist items grouped by product.product ID
        items_by_product = {}
        for item in self.item_ids:
            if item.product_id:
                items_by_product.setdefault(item.product_id.id, self.env['product.pricelist.item'])
                items_by_product[item.product_id.id] |= item
            elif item.product_tmpl_id:
                for variant in item.product_tmpl_id.product_variant_ids:
                    items_by_product.setdefault(variant.id, self.env['product.pricelist.item'])
                    items_by_product[variant.id] |= item

        if not items_by_product:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Vendor Prices',
                    'message': 'No products found in this pricelist to sync.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # Find purchase order lines for products present in this pricelist
        # where PO is confirmed/done and has a posted vendor bill
        domain = [
            ('order_id.state', 'in', ['purchase', 'done']),
            ('order_id.invoice_ids.state', '=', 'posted'),
            ('product_id', 'in', list(items_by_product.keys())),
        ]
        
        # Fetch matching PO lines and sort by purchase order date descending to get the latest unit price
        po_lines = self.env['purchase.order.line'].search(domain, order='id desc')
        po_lines = po_lines.sorted(key=lambda l: (l.order_id.date_order or l.create_date, l.id), reverse=True)

        latest_product_prices = {}
        for line in po_lines:
            product_id = line.product_id.id
            if product_id not in latest_product_prices:
                latest_product_prices[product_id] = line.price_unit

        if not latest_product_prices:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sync Vendor Prices',
                    'message': 'No qualified Purchase Orders with posted Vendor Bills were found for products in this pricelist.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        default_percentage = self.tier_id.percentage if (self.tier_id and self.tier_id.percentage) else 0.0
        updated_items = self.env['product.pricelist.item']

        for product_id, latest_cost in latest_product_prices.items():
            items = items_by_product.get(product_id, self.env['product.pricelist.item'])
            for item in items:
                if item not in updated_items:
                    perc = item.percentage_extra if item.percentage_extra else default_percentage
                    new_fixed_price = latest_cost * (1.0 + (perc / 100.0))
                    item.write({
                        'vendor_cost': latest_cost,
                        'percentage_extra': perc,
                        'fixed_price': new_fixed_price,
                    })
                    updated_items |= item

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Vendor Prices',
                'message': f'Vendor prices synced successfully! Updated {len(updated_items)} item(s).',
                'type': 'success',
                'sticky': False,
            }
        }
