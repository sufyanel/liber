# -*- coding: utf-8 -*-
import json
from urllib.parse import quote

from odoo import models
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _liber_has_quote_tag(self):
        self.ensure_one()
        return any(tag.name == "Request Quote" for tag in self.product_tag_ids)

    def _liber_user_can_shop(self):
        """Any authenticated (non-public) user may purchase."""
        user = self.env.user
        if request and getattr(request, "env", None):
            user = request.env.user
        return bool(user) and not user._is_public()

    def _liber_product_is_cartable(self):
        """Product-level cart eligibility, independent of authentication."""
        self.ensure_one()
        if self._liber_has_quote_tag():
            return False
        if not self._is_add_to_cart_possible():
            return False
        website = self.env["website"].get_current_website()
        if website.prevent_zero_price_sale and not self.list_price:
            return False
        return True

    def _liber_show_add_to_cart(self):
        self.ensure_one()
        return self._liber_user_can_shop() and self._liber_product_is_cartable()

    def _liber_show_sign_in_to_buy(self):
        """Anonymous CTA when the product would otherwise be purchasable."""
        self.ensure_one()
        return (not self._liber_user_can_shop()) and self._liber_product_is_cartable()

    def _liber_signin_buy_url(self):
        """Login URL that returns the shopper to this product after auth."""
        self.ensure_one()
        redirect = self.website_url or "/shop"
        return "/web/login?redirect=%s" % quote(redirect, safe="")

    def _liber_show_request_quote(self):
        self.ensure_one()
        if self._liber_has_quote_tag():
            return True
        if not self._is_add_to_cart_possible():
            return True
        website = self.env["website"].get_current_website()
        if website.prevent_zero_price_sale and not self.list_price:
            return True
        try:
            variant = self.product_variant_id
            if variant and hasattr(variant, "allow_out_of_stock_order"):
                if not variant.allow_out_of_stock_order and variant._is_sold_out():
                    return True
        except Exception:
            pass
        return False

    def _liber_get_seo_meta_title(self):
        self.ensure_one()
        parts = []
        if self.default_code:
            parts.append(self.default_code)
        if self.name:
            parts.append(self.name)
        title = " — ".join(parts) if parts else (self.name or "Product")
        return f"{title} | Liber"

    def _liber_get_seo_meta_description(self):
        self.ensure_one()
        desc = (self.description_sale or self.name or "").strip()
        if len(desc) > 155:
            desc = desc[:152].rsplit(" ", 1)[0] + "…"
        return desc or f"Industrial spare part from Liber Holdings: {self.name}"

    def _default_website_meta(self):
        res = super()._default_website_meta()
        title = self._liber_get_seo_meta_title()
        description = self._liber_get_seo_meta_description()
        res["default_opengraph"]["og:title"] = title
        res["default_twitter"]["twitter:title"] = title
        res["default_opengraph"]["og:description"] = description
        res["default_twitter"]["twitter:description"] = description
        res["default_meta_description"] = description
        return res

    def _liber_product_json_ld(self, website):
        self.ensure_one()
        base = (website.domain or "").rstrip("/")
        if not base:
            base = ""
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
                "url": f"{base}{self.website_url}",
                "priceCurrency": website.currency_id.name,
                "price": str(self.list_price),
                "availability": "https://schema.org/InStock",
            },
        }
        return json.dumps(data, ensure_ascii=True)
