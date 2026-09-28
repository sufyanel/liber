# -*- coding: utf-8 -*-


def _configure_rbc_industrial(env, website=None):
    """Apply RBC Industrial configuration, website theme_id, COW page overrides, and color palette."""
    if not website:
        website = env["website"].sudo().search([("name", "ilike", "RBC Industrial")], limit=1)
    if not website:
        website = env["website"].sudo().browse(4) # Website ID 4 fallback
    if not website or not website.exists():
        website = env["website"].sudo().get_current_website(fallback=False)
    if not website:
        return

    # Set theme_id on target website
    theme_module = env["ir.module.module"].sudo().search([("name", "=", "rbc_industrial_theme")], limit=1)
    if theme_module and website.theme_id != theme_module:
        website.theme_id = theme_module.id

    Tag = env["product.tag"].sudo()
    if not Tag.search([("name", "=", "Request Quote")], limit=1):
        Tag.create({"name": "Request Quote"})

    # Setup COW pages for the website
    _setup_website_pages(env, website)

    # Ensure website.contactus views are valid
    _heal_contactus_views(env)

    # Force frontend asset bundles to rebuild
    env["ir.attachment"].sudo().search([
        ("name", "ilike", "web.assets_frontend%"),
    ]).unlink()
    env.registry.clear_cache()

    # Set RBC Industrial website primary palette
    _rbc_set_color_palette(env, website)


def _heal_contactus_views(env):
    """Ensure all website.contactus views retain a valid wrap element so xpaths locate it."""
    View = env["ir.ui.view"].sudo()
    base_contactus = View.search([("key", "=", "website.contactus"), ("website_id", "=", False)], limit=1)
    if not base_contactus or not base_contactus.arch_db:
        return
    base_arch = base_contactus.arch_db
    cow_views = View.search([("key", "=", "website.contactus"), ("id", "!=", base_contactus.id)])
    for cv in cow_views:
        arch_str = str(cv.arch_db)
        if "id=\"wrap\"" not in arch_str and "id='wrap'" not in arch_str:
            cv.write({"arch_db": base_arch})
            if cv.website_id and (cv.website_id.name == "Liber Holdings" or cv.website_id.id == 1):
                try:
                    cv.website_id._liber_style_contact_page()
                except Exception:
                    pass


def _setup_website_pages(env, website):
    """Ensure site-specific COW views render theme templates when the theme is applied."""
    View = env["ir.ui.view"].sudo()
    Page = env["website.page"].sudo()

    pages_config = [
        {
            "url": "/",
            "key": "website.home-rbc-industrial",
            "name": "Home - RBC Industrial",
            "body": "rbc_industrial_theme.rbc_homepage_body",
        },
        {
            "url": "/home",
            "key": "website.home-rbc-industrial",
            "name": "Home - RBC Industrial",
            "body": "rbc_industrial_theme.rbc_homepage_body",
        },
        {
            "url": "/about-us",
            "key": "website.about-us",
            "name": "About Us",
            "body": "rbc_industrial_theme.rbc_aboutus_body",
        },
        {
            "url": "/",
            "key": "website.industries",
            "name": "Industries Served",
            "body": "rbc_industrial_theme.rbc_industries_body",
        },
    ]

    for cfg in pages_config:
        arch = f"""<t t-name="{cfg['key']}">
    <t t-call="website.layout">
        <t t-call="{cfg['body']}"/>
    </t>
</t>"""
        # Search site-specific view
        view = View.search([
            ("website_id", "=", website.id),
            ("key", "=", cfg["key"]),
        ], limit=1)

        if not view:
            # Search page by URL and website
            page = Page.search([
                ("website_id", "=", website.id),
                ("url", "=", cfg["url"]),
            ], limit=1)
            if page and page.view_id:
                view = page.view_id

        if view:
            view.write({"arch_db": arch})
        else:
            # Create view and page if not existing
            new_view = View.create({
                "name": cfg["name"],
                "type": "qweb",
                "key": cfg["key"],
                "website_id": website.id,
                "arch_db": arch,
            })
            Page.create({
                "name": cfg["name"],
                "url": cfg["url"],
                "view_id": new_view.id,
                "website_id": website.id,
                "is_published": True,
            })


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
