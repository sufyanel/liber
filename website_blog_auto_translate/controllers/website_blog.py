from odoo import tools

from odoo.addons.website_blog.controllers.main import WebsiteBlog


class WebsiteBlogAutoTranslate(WebsiteBlog):
    """Translates what a page is about to render, before it renders it.

    The listing shows a teaser cut out of ``content``, so the posts it lists
    need their body translated too; the "next article" link only shows a title,
    so it is kept to that field.
    """

    def _prepare_blog_values(self, *args, **kwargs):
        values = super()._prepare_blog_values(*args, **kwargs)
        if not isinstance(values, dict):
            return values  # a redirect, e.g. when a tag slug went stale
        (values["first_post"] | values["posts"])._auto_translate()
        values["blogs"]._auto_translate()
        for key in ("other_tags", "tag_category"):
            # these are lazy on purpose in the core controller: only translate
            # them if the template really asks for them
            values[key] = tools.lazy(
                lambda records=values[key]: self._auto_translate_sorted(records)
            )
        return values

    def blog_post(self, blog, blog_post, **post):
        response = super().blog_post(blog, blog_post, **post)
        qcontext = getattr(response, "qcontext", None)
        if not qcontext:
            return response  # a redirect
        qcontext["blog_post"]._auto_translate()
        qcontext["blog"]._auto_translate()
        qcontext["tags"]._auto_translate()
        if qcontext.get("next_post"):
            qcontext["next_post"]._auto_translate(fnames=["name"])
        return response

    def _auto_translate_sorted(self, records):
        """Translate a sorted list of records, then sort it on the translation."""
        if not records:
            return records
        recordset = records[0].browse([record.id for record in records])
        recordset._auto_translate()
        return sorted(recordset, key=lambda record: (record.name or "").upper())
