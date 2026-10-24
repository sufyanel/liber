from odoo import http, tools

from odoo.addons.http_routing.models.ir_http import url_for

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

    # The bare @http.route() is required on any override of a routed method.
    # Without it Odoo wraps the method in a functools.partial, which has no
    # ``original_endpoint`` and makes /sitemap.xml fail with a 500 on every site.
    @http.route()
    def blog_post(self, blog, blog_post, **post):
        response = super().blog_post(blog, blog_post, **post)
        qcontext = getattr(response, "qcontext", None) or {}
        post_record = qcontext.get("blog_post")
        if not post_record:
            # not the post page (a redirect, e.g. an old URL naming the blog
            # the post was moved out of): hand it back, never a 500. Keep the
            # visitor's language on the redirect (/es_MX/... stays /es_MX/...).
            location = getattr(response, "headers", {}).get("Location")
            if location and location.startswith("/") and getattr(response, "status_code", 0) in (301, 302, 303):
                response.headers["Location"] = url_for(location)
            return response
        post_record._auto_translate()
        if qcontext.get("blog"):
            qcontext["blog"]._auto_translate()
        if qcontext.get("tags"):
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
