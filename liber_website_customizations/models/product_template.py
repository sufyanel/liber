from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    seo_description = fields.Html(string='SEO Description', sanitize=False)
