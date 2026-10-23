# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from .product_pricelist_item import price_from_margin


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    tier_id = fields.Many2one(
        'pricelist.tier',
        string='Tier',
        help='Select tier assigned to this pricelist. Its gross margin is the default for the pricelist lines.',
    )
    cost_rule = fields.Selection(
        [('priority', 'Vendor price list first'),
         ('highest', 'Higher of vendor price list and last vendor bill')],
        string='Cost Rule', default='priority', required=True,
        help='How Sync Vendor Prices picks the cost:\n'
             '- Vendor price list first: the top line of the product\'s vendor price list, else the latest posted '
             'vendor bill, else the average cost (Dale, 7 and 16 Oct 2026).\n'
             '- Higher of vendor price list and last vendor bill: whichever is higher, so a tariff increase entered on '
             'the vendor price list is never undercut by an older bill; else the average cost (Dale, 1 Oct 2026).\n'
             'The average cost is only read, never changed.',
    )

    @api.onchange('tier_id')
    def _onchange_tier_id_apply_percentage(self):
        if self.tier_id and self.tier_id.percentage:
            margin = self.tier_id.percentage
            for item in self.item_ids:
                item.percentage_extra = margin
                if item.vendor_cost:
                    item.fixed_price = price_from_margin(item.vendor_cost, margin)

    def write(self, vals):
        res = super().write(vals)
        if 'tier_id' in vals:
            for pricelist in self:
                if pricelist.tier_id and pricelist.tier_id.percentage:
                    margin = pricelist.tier_id.percentage
                    for item in pricelist.item_ids:
                        new_vals = {'percentage_extra': margin}
                        if item.vendor_cost:
                            new_vals['fixed_price'] = price_from_margin(item.vendor_cost, margin)
                        item.write(new_vals)
        return res

    def action_sync_vendor_prices(self):
        """Price every saleable product from its vendor cost and the gross margin.

        Cost per product (Dale, 7 Oct 2026): top line of the vendor price list, else the latest posted vendor
        bill, else the average cost. Existing lines are updated; products without a line get one, so every
        product with a cost can be listed on the website. Products with no cost at all are skipped and counted.
        """
        self.ensure_one()
        company = self.company_id or self.env.company
        default_margin = self.tier_id.percentage if (self.tier_id and self.tier_id.percentage) else 0.0

        by_product, by_template = {}, {}
        for item in self.item_ids:
            if item.applied_on == '0_product_variant' and item.product_id:
                by_product[item.product_id.id] = item
            elif item.applied_on == '1_product' and item.product_tmpl_id:
                by_template[item.product_tmpl_id.id] = item

        products = self.env['product.product'].with_company(company).search([
            ('sale_ok', '=', True),
            ('company_id', 'in', [False, company.id]),
        ])
        counts = {'updated': 0, 'created': 0, 'skipped': 0,
                  'vendor_pricelist': 0, 'vendor_bill': 0, 'average_cost': 0}
        to_create = []
        skipped_names = []
        for product in products:
            cost, source = product._liber_vendor_cost(company, rule=self.cost_rule)
            if not cost or cost <= 0:
                counts['skipped'] += 1
                skipped_names.append(product.default_code or product.display_name)
                continue
            counts[source] += 1
            item = by_product.get(product.id)
            if not item:
                template_item = by_template.get(product.product_tmpl_id.id)
                # a product-level line is only reused when the product has a single variant
                if template_item and product.product_tmpl_id.product_variant_count == 1:
                    item = template_item
            margin = (item.percentage_extra if item and item.percentage_extra else default_margin)
            vals = {
                'vendor_cost': cost,
                'percentage_extra': margin,
                'fixed_price': price_from_margin(cost, margin),
                'cost_source': source,
                'compute_price': 'fixed',
            }
            if item:
                item.write(vals)
                counts['updated'] += 1
            else:
                vals.update({'pricelist_id': self.id, 'applied_on': '0_product_variant', 'product_id': product.id,
                             'product_tmpl_id': product.product_tmpl_id.id})
                to_create.append(vals)
        if to_create:
            self.env['product.pricelist.item'].create(to_create)
            counts['created'] = len(to_create)

        if not (counts['updated'] or counts['created']):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Vendor Prices'),
                    'message': _('No product has a vendor price list line, a posted vendor bill or an average cost.'),
                    'type': 'warning',
                    'sticky': False,
                },
            }
        message = _(
            "%(updated)s line(s) updated, %(created)s created. Cost taken from: vendor price list %(vendor_pricelist)s, "
            "vendor bill %(vendor_bill)s, average cost %(average_cost)s. %(skipped)s product(s) skipped (no cost anywhere).",
            **counts)
        if skipped_names:
            shown = ', '.join(skipped_names[:25])
            more = len(skipped_names) - 25
            message += ' ' + _('Skipped: %s') % shown + ((' ' + _('and %s more.') % more) if more > 0 else '.')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': _('Sync Vendor Prices'), 'message': message, 'type': 'success', 'sticky': True},
        }
