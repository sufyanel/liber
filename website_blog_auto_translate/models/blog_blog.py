from odoo import models


class Blog(models.Model):
    _name = "blog.blog"
    _inherit = ["blog.blog", "blog.auto.translate.mixin"]

    _auto_translate_fields = (
        "name",
        "subtitle",
        "content",
        "website_meta_title",
        "website_meta_description",
        "website_meta_keywords",
    )
