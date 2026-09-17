{
    "name": "Liber Holdings Website Theme",
    "summary": "Enterprise Website Theme & Design System for Liber Holdings",
    "description": """
        Custom enterprise website theme for Liber Holdings with multi-website support,
        scoped palette assets, dynamic color customization, and B2B eCommerce layout templates.
    """,
    "category": "Theme/Ecommerce",
    "license": "LGPL-3",
    "version": "17.0.1.25",
    "author": "Axiom World",
    "website": "https://www.liberholdings.com",
    "depends": [
        "website",
        "website_blog",
        "website_sale",
        "website_sale_stock",
        "website_crm",
    ],
    "data": [
        "data/product_tag_data.xml",
        "data/website_data.xml",
        "data/website_menu_data.xml",
        "views/templates_header.xml",
        "views/templates_footer.xml",
        "views/templates_homepage.xml",
        "views/templates_shop.xml",
        "views/templates_product.xml",
        "views/templates_quote.xml",
        "views/templates_blog.xml",
        "views/templates_seo.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "liber_holdings_theme/static/src/css/theme.css",
            "liber_holdings_theme/static/src/js/theme.js",
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


