from odoo import models


class BlogTag(models.Model):
    _name = "blog.tag"
    _inherit = ["blog.tag", "blog.auto.translate.mixin"]

    _auto_translate_fields = ("name",)
