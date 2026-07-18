# -*- coding: utf-8 -*-


def _configure_liber_holdings(env):
    """Apply Liber Holdings domain, contact redirect helpers, category typo fix."""
    website = env["website"].sudo().browse(1)
    if not website.exists():
        website = env["website"].sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
    if not website:
        return

    vals = {}
    # Do not force production domain on every upgrade — that breaks localhost
    # Website editing (Odoo redirects to website.domain). Set only when empty.
    if not website.domain:
        vals["domain"] = "https://www.liberholdings.com"
    if website.google_analytics_key and str(website.google_analytics_key).startswith("UA-"):
        vals["google_analytics_key"] = False
    if website.cdn_url and not website.cdn_activated:
        vals["cdn_activated"] = True
    if vals:
        website.write(vals)

    Tag = env["product.tag"].sudo()
    if not Tag.search([("name", "=", "Request Quote")], limit=1):
        Tag.create({"name": "Request Quote"})

    Category = env["product.public.category"].sudo()
    typo = Category.search([("name", "=", "Conveyor Componernts")], limit=1)
    if typo:
        typo.name = "Conveyor Components"

    # Icon-only stock ATC conflicts with Liber text CTAs / duplicate chrome
    View = env["ir.ui.view"].sudo().with_context(active_test=False)
    for view in View.search([("key", "=", "website_sale.products_add_to_cart")]):
        if view.active:
            view.write({"active": False})

    # Force frontend asset bundles to rebuild
    env["ir.attachment"].sudo().search([
        ("name", "ilike", "web.assets_frontend%"),
    ]).unlink()
    env.registry.clear_cache()

    # Set Liber Holdings website primary palette (replaces Odoo purple #714B67)
    _liber_set_holdings_color_palette(env, website)


def _liber_set_holdings_color_palette(env, website):
    """Write website SCSS color palette so o-color-1 / primary is Liber red."""
    import base64

    scss = """\
$o-user-color-palette: map-merge($o-user-color-palette, o-map-omit((
    'o-color-1': #B8322A,
    'o-color-2': #962820,
    'o-color-3': #F4F5F6,
    'o-color-4': #FFFFFF,
    'o-color-5': #1A1C1E,
    'o-cc1-btn-primary': 'o-color-1',
    'o-cc1-link': 'o-color-1',
    // -- hook --
)));
"""
    Att = env["ir.attachment"].sudo()
    url = "/_custom/web.assets_frontend/website/static/src/scss/options/colors/user_color_palette.scss"
    att = Att.search([
        ("url", "=", url),
        ("website_id", "=", website.id),
    ], limit=1)
    vals = {
        "name": "user_color_palette.scss",
        "type": "binary",
        "mimetype": "text/scss",
        "datas": base64.b64encode(scss.encode("utf-8")),
        "res_model": "ir.ui.view",
        "url": url,
        "website_id": website.id,
    }
    if att:
        att.write(vals)
    else:
        Att.create(vals)


def post_init_hook(env):
    _configure_liber_holdings(env)
