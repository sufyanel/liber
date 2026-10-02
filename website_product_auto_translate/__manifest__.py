{
    "name": "Website Product Auto-Translate (es_MX)",
    "summary": "Translates product descriptions into Spanish (Mexico) in the background, with the RBC / Tooling Components vocabulary",
    "version": "17.0.1.0.0",
    "category": "Website/Website",
    "license": "LGPL-3",
    "author": "Axiom World",
    "depends": ["website_sale"],
    "external_dependencies": {"python": ["deep_translator"]},
    "data": ["data/ir_cron.xml", "views/product_views.xml"],
    "installable": True,
}
