# -*- coding: utf-8 -*-
import json
import re
import logging

from markupsafe import Markup

from odoo import models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _liber_product_jsonld(self):
        """Return a schema.org Product JSON-LD string for this product.

        Built only from fields that are stable across Odoo 17–19 so the shop
        product page cannot break on an upgrade. Any unexpected error is
        swallowed and an empty string returned — SEO markup must never take a
        page down.

        Emits: name, sku, mpn (from Internal Reference), description, brand
        (only if a product-brand field is present), image, and an Offer with
        the list price, currency, availability and canonical URL.

        NOTE: the price used is the product's base sales price (list_price).
        It is a safe, stable value; it does not reflect per-pricelist or
        tax-inclusive pricing. If you need the exact website-computed price in
        the schema, extend this method with combination_info from the template.
        """
        self.ensure_one()
        try:
            website = self.env['website'].get_current_website()
        except Exception:
            website = self.env['website'].search([], limit=1)

        try:
            base_url = website.get_base_url() if website else self.get_base_url()
        except Exception:
            base_url = ''

        # Currency: website company first, then product currency, then USD.
        currency = False
        try:
            if website and website.company_id:
                currency = website.company_id.currency_id
        except Exception:
            currency = False
        if not currency:
            currency = getattr(self, 'currency_id', False)
        currency_name = currency.name if currency else 'USD'

        data = {
            '@context': 'https://schema.org/',
            '@type': 'Product',
            'name': self.name or '',
        }

        # MPN / SKU from the Internal Reference.
        if self.default_code:
            data['sku'] = self.default_code
            data['mpn'] = self.default_code

        # Description — prefer the eCommerce description, strip any HTML tags.
        raw_desc = ''
        for field_name in ('description_ecommerce', 'website_description', 'description_sale'):
            val = getattr(self, field_name, False)
            if val:
                raw_desc = val
                break
        if raw_desc:
            text = re.sub(r'<[^>]+>', ' ', str(raw_desc))
            text = re.sub(r'\s+', ' ', text).strip()
            if text:
                data['description'] = text[:5000]

        # Brand — only if a product-brand style field exists on the record.
        brand_name = ''
        brand_rec = getattr(self, 'product_brand_id', False)
        if brand_rec:
            brand_name = getattr(brand_rec, 'name', '') or ''
        if not brand_name:
            try:
                if website and website.company_id:
                    brand_name = website.company_id.name or ''
            except Exception:
                brand_name = ''
        if brand_name:
            data['brand'] = {'@type': 'Brand', 'name': brand_name}

        # Image (public product image endpoint).
        try:
            if self.id:
                data['image'] = '%s/web/image/product.template/%s/image_1024' % (base_url, self.id)
        except Exception:
            pass

        # Offer.
        try:
            price = round(float(self.list_price or 0.0), 2)
        except Exception:
            price = 0.0

        product_url = ''
        try:
            product_url = base_url + (self.website_url or '')
        except Exception:
            product_url = base_url

        offer = {
            '@type': 'Offer',
            'price': price,
            'priceCurrency': currency_name,
            'availability': 'https://schema.org/InStock',
        }
        if product_url:
            offer['url'] = product_url
        data['offers'] = offer

        try:
            payload = json.dumps(data, ensure_ascii=False)
            # Prevent any "</script>" breakout; "<\/" is valid inside JSON.
            payload = payload.replace('</', '<\\/')
            # Markup => QWeb t-out emits the JSON raw (no HTML entity escaping).
            return Markup(payload)
        except Exception:
            _logger.warning('Liber: failed to serialise product JSON-LD for %s', self.id)
            return ''
