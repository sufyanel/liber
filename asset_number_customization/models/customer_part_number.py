from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError

class CustomerPartNumber(models.Model):
    _name = "customer.part.number"
    _description = "Product Part Number"

    product_template_id = fields.Many2one('product.template', string='Product')
    partner_id = fields.Many2one('res.partner', string='Customer Name')
    asset_part_number = fields.Char(string='Asset Part No')
    addition_date = fields.Date(string='Addition Date', default=datetime.today())
    user_id = fields.Many2one('res.users', string='Added By', default=lambda self: self.env.user)
    last_sale_order_number = fields.Char(string='Last Sales Order No.')

