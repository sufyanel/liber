from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class ProductTemplateExt(models.Model):
    _inherit = 'product.template'

    product_template_sale_ids = fields.One2many('product.template.sales', 'product_template_id')




class ProductTemplateSales(models.Model):
    _name = "product.template.sales"
    _description = "Product Template Sales Section"

    product_template_id = fields.Many2one('product.template', string='Product')
    partner_ids = fields.Many2many('res.partner', string='Customer Name')
    asset_part_number = fields.Char(string='Asset Part No')
    addition_date = fields.Date(string='Addition Date',  default=datetime.today())
    user_id = fields.Many2one('res.users', string='Added By',default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        customer_part_record_set = self.env['customer.part.number']
        res = super(ProductTemplateSales, self).create(vals)
        for record in res:
            for rec in record.partner_ids:
                customer_part_record_set.create({
                    'product_template_id': record.product_template_id.id,
                    'partner_id': rec.id if rec.id else False,
                    'asset_part_number': record.asset_part_number if record.asset_part_number else '',
                    # 'last_purchase_order': res.last_purchase_order if res.last_purchase_order else '',
                })
        return res