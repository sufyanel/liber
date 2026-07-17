def _enable_shop_attribute_views(env):
    """Activate left + top attribute filter options on every website (COW-safe)."""
    keys = (
        "website_sale.products_attributes",
        "website_sale.products_attributes_top",
    )
    for website in env["website"].sudo().search([]):
        website_env = website.with_context(website_id=website.id)
        for key in keys:
            view = website_env.viewref(key, raise_if_not_found=False)
            if view and not view.active:
                view.with_context(website_id=website.id).write({"active": True})


def _tune_attribute_display(env):
    """Use a dropdown for high-cardinality Rate values in shop filters."""
    rate = env["product.attribute"].sudo().search(
        [("name", "ilike", "Rate (lbs/in)")],
        limit=1,
    )
    if rate and rate.display_type != "select":
        rate.display_type = "select"


def post_init_hook(env):
    _enable_shop_attribute_views(env)
    _tune_attribute_display(env)
