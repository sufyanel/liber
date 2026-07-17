{
    "name": "Liber Website Customizations",
    "summary": "This module will help to show custom snippets for website.",
    "description": "This module will help to show custom snippets for website.",
    "category": "Website/Liber Website Customizations",
    "license": "LGPL-3",
    "version": "17.0.1.1",
    "author": "Axiom World",
    "sequence": -1,
    "website_url": "https://axiomworld.net",
    "maintainer": "Axiom World",
    "depends": ["website", "website_sale"],
    "data": [
        "views/snippets.xml",
        "views/shop_filters.xml",
    ],
    "assets": {
        "web.assets_frontend": ["liber_website_customizations/static/src/scss/**"]
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "auto_install": False,
    "application": True,
}
