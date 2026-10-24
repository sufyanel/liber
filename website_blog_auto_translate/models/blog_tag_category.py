from odoo import models


class BlogTagCategory(models.Model):
    _name = "blog.tag.category"
    _inherit = ["blog.tag.category", "blog.auto.translate.mixin"]

    _auto_translate_fields = ("name",)
