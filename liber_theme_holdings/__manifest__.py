{
    "name": "Liber Holdings Theme",
    "summary": "Modern industrial design system for Liber Holdings website",
    "description": """
        Brand-first industrial B2B theme for Liber Holdings:
        design tokens, header/nav CTAs, homepage, shop cards,
        hybrid Cart/Quote CTAs, SEO helpers, and performance assets.
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
        "liber_website_customizations",
    ],
    "data": [
        "data/product_tag_data.xml",
        "data/website_data.xml",
        "data/website_menu_data.xml",
        "data/assets.xml",
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
            "liber_theme_holdings/static/src/css/theme.css",
            "liber_theme_holdings/static/src/js/theme.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
