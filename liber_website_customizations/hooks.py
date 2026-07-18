def _cleanup_hybrid_filter_views(env):
    """Drop leftover Brand-only left-rail inherits from the previous UX."""
    View = env["ir.ui.view"].sudo()
    leftovers = View.search(
        [
            (
                "key",
                "=",
                "liber_website_customizations.products_attributes_brand_only",
            )
        ]
    )
    if leftovers:
        leftovers.unlink()


def _set_shop_filter_views(env):
    """Force drawer-only shop filters on every website (COW-safe)."""
    enable = (
        "website_sale.products_attributes_top",
        "website_sale.filter_products_price",
        "website_sale.filter_products_tags",
        "website_sale.products_categories_top",
    )
    disable = (
        "website_sale.products_categories",
        "website_sale.products_attributes",
    )
    _cleanup_hybrid_filter_views(env)
    for website in env["website"].sudo().search([]):
        website_env = website.with_context(website_id=website.id)
        for key in enable:
            view = website_env.viewref(key, raise_if_not_found=False)
            if view and not view.active:
                view.with_context(website_id=website.id).write({"active": True})
        for key in disable:
            view = website_env.viewref(key, raise_if_not_found=False)
            if view and view.active:
                view.with_context(website_id=website.id).write({"active": False})


def _tune_attribute_display(env):
    """Use a dropdown for high-cardinality Rate values in shop filters."""
    rate = env["product.attribute"].sudo().search(
        [("name", "ilike", "Rate (lbs/in)")],
        limit=1,
    )
    if rate and rate.display_type != "select":
        rate.display_type = "select"


def post_init_hook(env):
    _set_shop_filter_views(env)
    _tune_attribute_display(env)


# Backwards-compatible alias used by older call sites / upgrades
_enable_shop_attribute_views = _set_shop_filter_views
