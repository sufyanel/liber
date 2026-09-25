{
    "name": "Threshold Report - Intercompany AP Allocation (Import)",
    "version": "17.0.1.1.0",
    "category": "Accounting",
    "summary": "Frontend-importable version: allocates Liber Holdings payables to "
               "RBC / Tooling for the Threshold Report Change in A/P",
    "author": "Axiom World",
    "website": "https://axiomworld.net",
    "license": "LGPL-3",
    "depends": ["threshold_report", "sale_purchase_stock"],
    "data": [
        "data/models.xml",
        "data/defaults.xml",
        "security/ir.model.access.csv",
        "security/rules.xml",
        "data/server_actions.xml",
        "views/views.xml",
    ],
    "installable": True,
    "application": False,
}
