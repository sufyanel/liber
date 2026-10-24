# -*- coding: utf-8 -*-
import werkzeug.exceptions

from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _pre_dispatch(cls, rule, arguments):
        """Liber Holdings: a product or category that belongs to another website 301s there (Dale, 9 Oct 2026).

        Odoo answers 404 for such a URL before any controller runs. On the Liber Holdings website the URL
        instead redirects to the subsidiary that sells the item, so the ranking it earned passes to RBC
        Industrial or Tooling Components. Every other website, and every other URL, behaves as before.
        """
        try:
            super()._pre_dispatch(rule, arguments)
        except werkzeug.exceptions.NotFound:
            path = (request.httprequest.path or "") if request and request.httprequest else ""
            if "/shop" not in path:
                raise
            from ..controllers.main import _liber_catalog_target, _liber_is_holding_website
            if not _liber_is_holding_website(request.env["website"].sudo().get_current_website()):
                raise
            for record in arguments.values():
                if isinstance(record, models.BaseModel) and record._name in ("product.template", "product.public.category"):
                    record = record.with_env(request.env).sudo()
                    if not record.exists():
                        raise
                    if record._name == "product.template":
                        target = _liber_catalog_target(product=record)
                    else:
                        target = _liber_catalog_target(category=record)
                    werkzeug.exceptions.abort(request.redirect(target, code=301, local=False))
            raise
