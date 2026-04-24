{
    "name": "Income Statement",
    "version": "17.0.1.0.7",
    "depends": ["base", "account", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "security/income_statement_budget_rules.xml",
        "views/income_statement_wizard_views.xml",
        "views/income_statement_budget_views.xml",
        "views/income_statement_account_mapping_views.xml",
        "views/menu_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
