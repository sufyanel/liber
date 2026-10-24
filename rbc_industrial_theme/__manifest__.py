{
    "name": "RBC Industrial Website Theme",
    "summary": "Mission Critical Industrial design for the RBC Industrial website (import-safe)",
    "description": """
RBC Industrial website design (Mission Critical Industrial brand): emergency
line-down bar, SDVOSB / Texas HUB badges, engineer-dense product catalog
(part number, description, category, top-4 specs, price, stock), compact
filters, spec-sheet product page with JSON-LD, compact Knowledge Base, contact /
quote forms creating CRM leads. Data-only: installable from Apps > Import Module.
Everything is scoped to the RBC Industrial website only.
    """,
    "category": "Website/Website",
    "license": "LGPL-3",
    "version": "17.0.10.5.2",
    "author": "Axiom World",
    "website": "https://www.rbc-industrial.com",
    "depends": [
        "website",
        "website_blog",
        "website_sale",
        "website_sale_stock",
        "website_crm",
        "liber_holdings_theme",
    ],
    "data": [
        "data/fields.xml",
        "views/layout.xml",
        "views/pages.xml",
        "views/shop.xml",
        "views/product.xml",
        "views/blog.xml",
        "views/website_form.xml",
        "views/liber_scope.xml",
        "views/ga4_lead.xml",
        "data/website_data.xml",
        "data/translations_es_mx.xml",
        "data/variant_documents.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "rbc_industrial_theme/static/src/js/product_translate_es.js",
        ],
        "web.assets_frontend": [
            "rbc_industrial_theme/static/src/css/theme.css",
            "rbc_industrial_theme/static/src/js/catalog.js",
            "rbc_industrial_theme/static/src/js/notification_compat.js",
        ],
    },
    "installable": True,
    "application": False,
}
