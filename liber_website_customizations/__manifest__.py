{
    "name": "Liber Website Customizations",
    "summary": "This module will help to show custom snippets for website.",
    "description": "This module will help to show custom snippets for website.",
    "category": "Website/Liber Website Customizations",
    "license": "LGPL-3",
    "version": "17.0.1.0",
    "author": "Momin Ali | Axiom World",
    "sequence": -1,
    "website_url": "https://axiomworld.net",
    "maintainer": "Axiom World",
    "depends": ["website", "website_sale", "website_sale_wishlist"],
    "data": ["views/snippets.xml", "views/product_seo_description.xml"],
    "assets": {
        "web.assets_frontend": ["liber_website_customizations/static/src/scss/**"]
    },
    "installable": True,
    "auto_install": False,
    "application": True
}
