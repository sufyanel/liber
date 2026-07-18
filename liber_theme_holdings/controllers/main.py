# -*- coding: utf-8 -*-
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale


class LiberWebsiteSale(WebsiteSale):
    """Require login for cart / checkout / payment (browse remains public)."""

    @http.route(
        ["/shop/cart"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def cart(self, access_token=None, revive="", **post):
        return super().cart(access_token=access_token, revive=revive, **post)

    @http.route(
        ["/shop/cart/update"],
        type="http",
        auth="user",
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
        auth="user",
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

    @http.route(
        ["/shop/cart/quantity"],
        type="json",
        auth="user",
        methods=["POST"],
        website=True,
        csrf=False,
    )
    def cart_quantity(self):
        return super().cart_quantity()

    @http.route(["/shop/cart/clear"], type="json", auth="user", website=True)
    def clear_cart(self):
        return super().clear_cart()

    @http.route(
        "/shop/cart/update_address",
        type="http",
        auth="user",
        methods=["POST"],
        website=True,
    )
    def update_cart_address(self, partner_id, mode="billing", **kw):
        return super().update_cart_address(partner_id, mode=mode, **kw)

    @http.route(
        ["/shop/address"],
        type="http",
        methods=["GET", "POST"],
        auth="user",
        website=True,
        sitemap=False,
    )
    def address(self, **kw):
        return super().address(**kw)

    @http.route(
        ["/shop/checkout"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def checkout(self, **post):
        return super().checkout(**post)

    @http.route(
        ["/shop/confirm_order"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def confirm_order(self, **post):
        return super().confirm_order(**post)

    @http.route(
        ["/shop/extra_info"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def extra_info(self, **post):
        return super().extra_info(**post)

    @http.route(
        "/shop/payment",
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def shop_payment(self, **post):
        return super().shop_payment(**post)

    @http.route(
        "/shop/payment/validate",
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def shop_payment_validate(self, sale_order_id=None, **post):
        return super().shop_payment_validate(sale_order_id=sale_order_id, **post)

    @http.route(
        "/shop/payment/transaction/<int:order_id>",
        type="json",
        auth="user",
        website=True,
    )
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        return super().shop_payment_transaction(order_id, access_token, **kwargs)

    @http.route(
        ["/shop/confirmation"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def shop_payment_confirmation(self, **post):
        return super().shop_payment_confirmation(**post)
