from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class SaleOrderLineExt(models.Model):
    _inherit = 'sale.order.line'

    asset_part_number = fields.Char(string='Customer Part No')

    @api.model_create_multi
    @api.model
    def create(self, vals):
        partner = self.env['sale.order'].search([('id', '=', vals.get('order_id', False))]).partner_id.id
        last_order_numver = self.env['sale.order'].search([('id', '=', vals.get('order_id', False))]).name
        product = self.env['product.product'].search([('id', '=', vals.get('product_id', False))]).product_tmpl_id.id

        customer_part_record_set = self.env['customer.part.number'].search(
            [('partner_id', '=', partner), ('product_template_id', '=', product)])

        res = super(SaleOrderLineExt, self).create(vals)
        if customer_part_record_set:
            customer_part_record_set.write({
                'last_sale_order_number': last_order_numver
            })
        else:
            pass
        return res

    # Compute Asset Part Number
    @api.onchange('product_id')
    def compute_asset_part_number(self):
        for rec in self:
            if rec.product_id:
                customer_part_set = self.env['customer.part.number'].search(
                    [('product_template_id', '=', rec.product_id.product_tmpl_id.id),
                     ('partner_id', '=', rec.order_id.partner_id.id)])
                if customer_part_set:
                    rec.asset_part_number = customer_part_set[0].asset_part_number or ''
