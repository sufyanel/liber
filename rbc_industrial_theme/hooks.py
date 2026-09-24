# -*- coding: utf-8 -*-


def _configure_rbc_industrial(env, website=None):
    """Apply RBC Industrial configuration and color palette."""
    if not website:
        website = env["website"].sudo().search([("name", "ilike", "RBC Industrial")], limit=1)
    if not website:
        website = env["website"].sudo().browse(4) # Website ID 4 fallback
    if not website or not website.exists():
        website = env["website"].sudo().get_current_website(fallback=False)
    if not website:
        return

    Tag = env["product.tag"].sudo()
    if not Tag.search([("name", "=", "Request Quote")], limit=1):
        Tag.create({"name": "Request Quote"})

    # Force frontend asset bundles to rebuild
    env["ir.attachment"].sudo().search([
        ("name", "ilike", "web.assets_frontend%"),
    ]).unlink()
    env.registry.clear_cache()

    # Set RBC Industrial website primary palette
    _rbc_set_color_palette(env, website)


def _rbc_set_color_palette(env, website):
    """Write website SCSS color palette for RBC Industrial (Gear Brown / Rotational Gold)."""
    import base64

    if not website:
        return

    scss = """\
$o-user-color-palette: map-merge($o-user-color-palette, o-map-omit((
    'o-color-1': #4A352C, // Primary Gear Brown
    'o-color-2': #FED37E, // Secondary Rotational Gold
    'o-color-3': #E9E8E8, // Light Gray
    'o-color-4': #FFFFFF,
    'o-color-5': #181818, // Near Black
    'o-cc1-btn-primary': 'o-color-2',
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
    _configure_rbc_industrial(env)


