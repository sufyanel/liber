{
    "name": "Globe Electric Supply Theme",
    "version": "17.0.2.3.0",
    "summary": "Website theme for Globe Electric Supply Co Inc: critical-infrastructure supply for rail, traffic and aviation",
    "description": """
Globe Electric Supply Co Inc website, built the way RBC Industrial and Tooling
Components were built: its own website record, its own flag, and the shared
Liber base layer switched off on this site.

Brand: "Always On". Graphite, Concrete and Voltage Yellow; Oswald headings,
Inter body; a 4px Voltage Yellow rule on the header and every certification panel.

Data only: installs through Apps > Import Module as well as through the
repository. Everything is built by a data action on install and on every
upgrade, so no page depends on a database-only edit.
""",
    "author": "Axiom World",
    "website": "https://globelectric.com",
    "category": "Theme/Corporate",
    "license": "LGPL-3",
    "depends": ["website_sale", "liber_holdings_theme", "website", "website_blog", "website_crm"],
    "data": [
        "data/fields.xml",
        "views/layout.xml",
        "views/pages_home.xml",
        "views/pages_government.xml",
        "views/pages_quote.xml",
        "views/pages_other.xml",
        "views/blog.xml",
        "views/catalog.xml",
        "views/catalog_shop.xml",
        "data/website_data.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "globe_electric_theme/static/src/css/theme.css",
            "globe_electric_theme/static/src/css/catalog.css",
            "globe_electric_theme/static/src/js/globe.js",
        ],
    },
    "installable": True,
    "application": False,
}
