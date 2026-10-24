# -*- coding: utf-8 -*-
import json
from urllib.parse import quote
from odoo import models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _liber_is_liber_website(self):
        """Check if the current request is for Liber Holdings website."""
        website = self.env["website"].get_current_website()
        return bool(website and "liber" in (website.name or "").lower())

    def _liber_has_quote_tag(self):
        self.ensure_one()
        return any(tag.name == "Request Quote" for tag in self.product_tag_ids)

    def _liber_user_can_shop(self):
        """Any authenticated (non-public) user may purchase on transactional websites."""
        user = self.env.user
        if request and getattr(request, "env", None):
            user = request.env.user
        return bool(user) and not user._is_public()

    def _liber_product_is_cartable(self):
        """Product-level cart eligibility."""
        self.ensure_one()
        if self._liber_has_quote_tag():
            return False
        if not self._is_add_to_cart_possible():
            return False
        website = self.env["website"].get_current_website()
        if website and website.prevent_zero_price_sale and not self.list_price:
            return False
        return True

    def _liber_show_add_to_cart(self):
        """On Liber Holdings, direct public checkout is disabled (view-only catalog to prevent SEO cannibalization with RBC Industrial)."""
        self.ensure_one()
        if self._liber_is_liber_website():
            return False
        return self._liber_user_can_shop() and self._liber_product_is_cartable()

    def _liber_show_sign_in_to_buy(self):
        """Show login prompt only if cartable and not on Liber Holdings view-only site."""
        self.ensure_one()
        if self._liber_is_liber_website():
            return False
        return (not self._liber_user_can_shop()) and self._liber_product_is_cartable()

    def _liber_signin_buy_url(self):
        """Login URL that returns the shopper to this product after auth."""
        self.ensure_one()
        redirect = self.website_url or "/shop"
        return "/web/login?redirect=%s" % quote(redirect, safe="")

    def _liber_show_request_quote(self):
        """All products on Liber Holdings show Request a Quote."""
        self.ensure_one()
        if self._liber_is_liber_website():
            return True
        if self._liber_has_quote_tag():
            return True
        if not self._is_add_to_cart_possible():
            return True
        website = self.env["website"].get_current_website()
        if website and website.prevent_zero_price_sale and not self.list_price:
            return True
        return False

    def _liber_get_top_spec_attributes(self, limit=4):
        """Extract top N product attributes formatted for technical parts list view."""
        self.ensure_one()
        specs = []
        for line in self.attribute_line_ids:
            attr_name = line.attribute_id.name or ""
            val_names = ", ".join(line.value_ids.mapped("name"))
            if attr_name and val_names:
                specs.append({
                    "attribute": attr_name,
                    "value": val_names,
                    "formatted": f"{attr_name}: {val_names}"
                })
            if len(specs) >= limit:
                break
        return specs

    def _liber_product_json_ld(self, website):
        """Generate structured JSON-LD microdata for product schema."""
        self.ensure_one()
        base = (website.domain or "").rstrip("/") if website else ""
        data = {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": self.name or "",
            "sku": self.default_code or str(self.id),
            "description": (self.description_sale or self.name or "")[:300],
            "image": f"{base}/web/image/product.template/{self.id}/image_1024",
            "brand": {"@type": "Brand", "name": "Liber"},
            "offers": {
                "@type": "Offer",
                "url": f"{base}{self.website_url}" if website else "",
                "priceCurrency": (
                    website.currency_id.name
                    if website and website.currency_id
                    else "USD"
                ),
                "price": str(self.list_price),
                "availability": "https://schema.org/InStock",
            },
        }
        return json.dumps(data, ensure_ascii=True)
