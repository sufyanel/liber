{
    "name": "Website Blog Auto Translate",
    "summary": "Machine-translate blog posts on the fly when a visitor switches the website language.",
    "category": "Website/Website",
    "license": "LGPL-3",
    "version": "17.0.2.0.0",
    "author": "Axiom World",
    "website_url": "https://axiomworld.net",
    "maintainer": "Axiom World",
    "depends": ["website_blog"],
    "external_dependencies": {"python": ["deep-translator"]},
    "data": [
        "views/blog_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
