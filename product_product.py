# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _liber_vendor_cost(self, company=None, rule='priority'):
        """Cost used for the website price, in the company currency and the product's unit of measure.

        Priority (Dale, 7 Oct 2026):
          1. the TOP line of the product's vendor price list (Purchase tab order - not the cheapest), because
             tariff changes make old bills inaccurate and buyers update the vendor price list;
          2. the latest posted vendor bill;
          3. the average cost on the product form.
        Returns (cost, source) with source in 'vendor_pricelist', 'vendor_bill', 'average_cost', or (0.0, False).

        rule='highest' (Dale, 1 Oct 2026): the higher of the vendor price list cost and the last vendor bill cost;
        when only one exists that one is used; the average cost remains the last fallback.
        """
        self.ensure_one()
        company = company or self.env.company
        pricelist_cost = self._liber_cost_from_vendor_pricelist(company)
        if rule != 'highest' and pricelist_cost:
            return pricelist_cost, 'vendor_pricelist'
        bill_cost = self._liber_cost_from_last_bill(company)
        if rule == 'highest' and (pricelist_cost or bill_cost):
            if pricelist_cost >= bill_cost:
                return pricelist_cost, 'vendor_pricelist'
            return bill_cost, 'vendor_bill'
        if bill_cost:
            return bill_cost, 'vendor_bill'
        # average cost - only read, never written (Dale: no change to a written-off part's average cost)
        cost = self.with_company(company).standard_price
        if cost:
            return cost, 'average_cost'
        return 0.0, False

    def _liber_cost_from_vendor_pricelist(self, company):
        """Top valid line of the vendor price list (Purchase tab order), in company currency and product UoM."""
        currency = company.currency_id
        today = fields.Date.context_today(self)
        for seller in self.seller_ids:
            if seller.product_id and seller.product_id != self:
                continue
            if seller.company_id and seller.company_id != company:
                continue
            if seller.date_start and seller.date_start > today:
                continue
            if seller.date_end and seller.date_end < today:
                continue
            if not seller.price:
                continue
            price = seller.price * (1.0 - (getattr(seller, 'discount', 0.0) or 0.0) / 100.0)
            if seller.currency_id and seller.currency_id != currency:
                price = seller.currency_id._convert(price, currency, company, today)
            if seller.product_uom and seller.product_uom != self.uom_id:
                price = seller.product_uom._compute_price(price, self.uom_id)
            return price
        return 0.0

    def _liber_cost_from_last_bill(self, company):
        """Unit cost on the latest posted vendor bill line, in company currency and product UoM."""
        currency = company.currency_id
        today = fields.Date.context_today(self)
        line = self.env['account.move.line'].sudo().search([
            ('product_id', '=', self.id),
            ('move_id.move_type', '=', 'in_invoice'),
            ('parent_state', '=', 'posted'),
            ('company_id', '=', company.id),
            ('display_type', '=', 'product'),
            ('price_unit', '>', 0),
        ], order='date desc, id desc', limit=1)
        if not line:
            return 0.0
        price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
        if line.currency_id and line.currency_id != currency:
            price = line.currency_id._convert(price, currency, company, line.date or today)
        if line.product_uom_id and line.product_uom_id != self.uom_id:
            price = line.product_uom_id._compute_price(price, self.uom_id)
        return price
