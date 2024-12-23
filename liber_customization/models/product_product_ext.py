from odoo import api, fields, models, _


class ProductProductExt(models.Model):
    _inherit = 'product.product'

    def get_product_multiline_description_sale(self):
        """ when select product only product's description will be selected in Sale order lines not with product name etc.
        """
        if self.description_sale:
            name = self.description_sale
        else:
            name = ''

        return name