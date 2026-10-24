from odoo import models


class BlogPost(models.Model):
    _name = "blog.post"
    _inherit = ["blog.post", "blog.auto.translate.mixin"]

    _auto_translate_fields = (
        "name",
        "subtitle",
        "content",
        "website_meta_title",
        "website_meta_description",
        "website_meta_keywords",
    )
