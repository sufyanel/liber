{
    "name": "RBC Industrial Website Theme",
    "summary": "Mission-Critical Industrial Theme for RBC Industrial",
    "description": """
        Mission-Critical B2B Theme for RBC Industrial with emergency line-down bar,
        SDVOSB & Texas HUB certification badges, custom layout sections, and engineer-led B2B eCommerce templates.
    """,
    "category": "Theme/Ecommerce",
    "license": "LGPL-3",
    "version": "17.0.1.00",
    "author": "Axiom World",
    "website": "https://www.rbc-industrial.com",
    "depends": [
        "website",
        "website_blog",
        "website_sale",
        "website_sale_stock",
        "website_crm",
    ],
    "data": [
        "data/website_data.xml",
        "data/website_menu_data.xml",
        "views/templates_header.xml",
        "views/templates_footer.xml",
        "views/templates_homepage.xml",
        "views/templates_about.xml",
        "views/templates_contact.xml",
        "views/templates_shop.xml",
        "views/templates_product.xml",
        "views/templates_quote.xml",
        "views/templates_blog.xml",
        "views/templates_seo.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "rbc_industrial_theme/static/src/css/theme.css",
            "rbc_industrial_theme/static/src/js/theme.js",
        ],
    },
    "images": [
        "home.png",
        "shop.png",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
}


