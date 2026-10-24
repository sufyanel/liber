# -*- coding: utf-8 -*-
from urllib.parse import quote

import logging
import traceback

import odoo
from odoo import fields, http
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website_sale.controllers.main import WebsiteSale


# Websites claimed by a sibling theme (RBC Industrial, Tooling Components).
LIBER_SIBLING_FLAGS = (
    "x_rbc_theme_active",
    "x_tc_theme_active",
    "x_tooling_theme_active",
    "x_tooling_components_theme_active",
    "x_globe_theme_active",
)


def _liber_is_sibling(website):
    return bool(website) and any(f in website._fields and website[f] for f in LIBER_SIBLING_FLAGS)


def _liber_sibling_page():
    """A sibling website (RBC Industrial, Tooling Components, Globe Electric) that defines its own page for this
    URL keeps it: the Liber controller only answers where the site has no page of its own."""
    if not _liber_is_sibling(request.website):
        return False
    page = request.env["website.page"].sudo().search(
        [("url", "=", request.httprequest.path), ("website_id", "=", request.website.id)], limit=1)
    return request.env["ir.http"]._serve_page() if page else False


def _liber_safe_render(template, values, label):
    """Render eagerly so a failure is caught here: the visitor gets a working fallback quote form instead of a
    bare "500: Internal Server Error", and the exact error is stored for "Liber: diagnose /quote"."""
    try:
        return request.make_response(request.render(template, values, lazy=False))
    except Exception:
        tb = traceback.format_exc()
        _logger.exception("Liber %s failed on website %s", label, request.website.id)
        try:
            request.env.cr.rollback()
        except Exception:
            pass
        try:
            with odoo.registry(request.env.cr.dbname).cursor() as cr2:
                env2 = odoo.api.Environment(cr2, odoo.SUPERUSER_ID, {})
                env2["ir.config_parameter"].set_param(
                    "liber_holdings_theme.last_quote_error",
                    "%s | website %s | %s\n%s" % (fields.Datetime.now(), request.website.id, request.httprequest.full_path, tb[-6000:]))
        except Exception:
            pass
        try:
            return request.make_response(request.render("liber_holdings_theme.quote_page_fallback", {}, lazy=False))
        except Exception:
            return request.make_response(
                '<html><body style="font-family:Arial,sans-serif;max-width:640px;margin:40px auto">'
                '<h1>Request a Quote</h1><p>Please email your part numbers and quantities to '
                '<a href="mailto:sales@liberindustrial.com">sales@liberindustrial.com</a> or call '
                '<a href="tel:+18327647979">(832) 764-7979</a>.</p><p><a href="/">Back to home</a></p></body></html>')


def _liber_is_holding_website(website):
    """Liber Holdings itself: a 'Liber' website that no sibling theme claims.
    'Liber Industrial' is a separate operating company and is excluded."""
    name = ((website and website.name) or "").lower()
    return bool(website) and "liber" in name and "industrial" not in name and not _liber_is_sibling(website)


def _liber_is_holding_site():
    """Check if the current website is Liber Holdings (view-only corporate site, no catalog)."""
    return _liber_is_holding_website(request.website)


def _liber_login_required():
    """On Liber Holdings, anonymous checkout is disabled entirely to avoid search engine cannibalization with RBC Industrial."""
    return _liber_is_holding_site() and request.env.user._is_public()


def _liber_login_redirect():
    return request.redirect("/web/login?redirect=%s" % quote(request.httprequest.full_path, safe=""))


def _liber_catalog_target(product=None, category=None):
    """Where a Liber Holdings catalog URL now points (Dale, 9 Oct 2026: Liber must not show products or
    compete with the subsidiaries in search). A product or category that belongs to RBC Industrial or
    Tooling Components goes to that site, so its ranking passes to the subsidiary; anything else goes to
    the Family of Companies section of the Liber home page."""
    fallback = "/#companies"
    sites = request.env["website"].sudo().search([]).filtered(lambda w: _liber_is_sibling(w) and w.domain)
    if not sites or not (product or category):
        return fallback
    site = request.env["website"]
    if product:
        product = product.sudo()
        if not product.is_published:
            return fallback
        if product.website_id in sites:
            site = product.website_id
        if not site:
            site = (product.public_categ_ids.mapped("website_id") & sites)[:1]
        if not site and product.company_id:
            site = sites.filtered(lambda w: w.company_id == product.company_id)[:1]
        path = "/shop/%s" % slug(product)
    else:
        category = category.sudo()
        if category.website_id in sites:
            site = category.website_id
        path = "/shop/category/%s" % slug(category)
    if not site:
        return fallback
    return site.domain.rstrip("/") + path


_logger = logging.getLogger(__name__)


class LiberWebsiteSale(WebsiteSale):
    """Disable public checkout on Liber Holdings (vendor & RFQ portal only), while preserving standard sale routes for sibling sites."""

    # Liber Holdings is a view-only corporate site (Dale, 9 Oct 2026): no catalog, no product pages, nothing that
    # competes with RBC Industrial or Tooling Components in search. (Disabled 2026-10-23: Liber Holdings shows its
    # own view-only catalog again, kept out of search by noindex + sitemap exclusion.) Catalog URLs answered 301 so whatever ranking
    # they had passes on. Sibling websites are untouched.
    @http.route()
    def shop(self, page=0, category=None, search="", min_price=0.0, max_price=0.0, ppg=False, **post):
        if False and _liber_is_holding_site():
            return request.redirect(_liber_catalog_target(category=category or None), code=301, local=False)
        return super().shop(page=page, category=category, search=search, min_price=min_price,
                            max_price=max_price, ppg=ppg, **post)

    @http.route()
    def product(self, product, category="", search="", **kwargs):
        if False and _liber_is_holding_site():
            return request.redirect(_liber_catalog_target(product=product), code=301, local=False)
        return super().product(product, category=category, search=search, **kwargs)

    @http.route(["/quote"], type="http", auth="public", website=True, sitemap=True)
    def liber_request_quote(self, product_id=None, **kw):
        """Dedicated Request a Quote landing page for Liber Holdings."""
        own = _liber_sibling_page()
        if own:
            return own
        product = None
        pid = str(product_id or "").strip()
        if pid.isdigit():
            try:
                product = request.env["product.template"].sudo().browse(int(pid)).exists() or None
            except Exception:  # never let a bad link break the quote form
                product = None
        return _liber_safe_render("liber_holdings_theme.quote_page", {
            "product": product,
            "product_id": product_id,
        }, "/quote")

    @http.route(["/quote-received"], type="http", auth="public", website=True, sitemap=False)
    def liber_quote_received(self, **kw):
        """Dedicated confirmation page for quote requests — prevents 404 tracking error discussed with Dale."""
        own = _liber_sibling_page()
        if own:
            return own
        return _liber_safe_render("liber_holdings_theme.quote_received_page", kw, "/quote-received")

    @http.route(["/brands"], type="http", auth="public", website=True, sitemap=True)
    def liber_brands_page(self, **kw):
        """Brands We Represent portfolio page."""
        own = _liber_sibling_page()
        if own:
            return own
        return request.render("liber_holdings_theme.brands_page", {})

    @http.route(
        ["/shop/cart"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def cart(self, access_token=None, revive="", **post):
        # On Liber Holdings, public cart is disabled to prioritize RFQs and prevent SEO cannibalization
        if _liber_is_holding_site():
            return request.redirect("/quote")
        return super().cart(access_token=access_token, revive=revive, **post)

    @http.route(
        ["/shop/cart/update"],
        type="http",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def cart_update(
        self,
        product_id,
        add_qty=1,
        set_qty=0,
        product_custom_attribute_values=None,
        no_variant_attribute_values=None,
        express=False,
        **kwargs
    ):
        if _liber_is_holding_site():
            return request.redirect("/quote?product_id=%s" % product_id)
        return super().cart_update(
            product_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            express=express,
            **kwargs
        )

    @http.route(
        ["/shop/cart/update_json"],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def cart_update_json(
        self,
        product_id,
        line_id=None,
        add_qty=None,
        set_qty=None,
        display=True,
        product_custom_attribute_values=None,
        no_variant_attribute_values=None,
        **kw
    ):
        if _liber_is_holding_site():
            raise AccessDenied("Purchasing directly on Liber Holdings is disabled. Please submit a Request for Quote.")
        return super().cart_update_json(
            product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            display=display,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kw
        )

    @http.route(["/shop/checkout"], type="http", auth="public", website=True, sitemap=False)
    def checkout(self, **post):
        if _liber_is_holding_site():
            return request.redirect("/quote")
        return super().checkout(**post)

    @http.route("/shop/payment", type="http", auth="public", website=True, sitemap=False)
    def shop_payment(self, **post):
        if _liber_is_holding_site():
            return request.redirect("/quote")
        return super().shop_payment(**post)
