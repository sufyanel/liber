# -*- coding: utf-8 -*-


def _configure_liber_holdings(env, website=None):
    """Apply Liber Holdings contact redirect helpers, category typo fix, and palette."""
    if not website:
        website = env["website"].sudo().search([("name", "ilike", "Liber Holdings")], limit=1)
    if not website:
        website = env["website"].sudo().get_current_website(fallback=False)
    if not website:
        return

    Tag = env["product.tag"].sudo()
    if not Tag.search([("name", "=", "Request Quote")], limit=1):
        Tag.create({"name": "Request Quote"})

    Category = env["product.public.category"].sudo()
    typo = Category.search([("name", "=", "Conveyor Componernts")], limit=1)
    if typo:
        typo.name = "Conveyor Components"

    # Force frontend asset bundles to rebuild
    env["ir.attachment"].sudo().search([
        ("name", "ilike", "web.assets_frontend%"),
    ]).unlink()
    env.registry.clear_cache()

    # Set Liber Holdings website primary palette
    _liber_set_holdings_color_palette(env, website)


def _liber_set_holdings_color_palette(env, website):
    """Write website SCSS color palette so o-color-1 / primary is Liber red for specific website."""
    import base64

    if not website:
        return

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

