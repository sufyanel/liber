{
    "name": "Income Statement",
    "version": "17.0.1.0.4",
    "depends": ["base", "account"],
    "data": [
        "security/ir.model.access.csv",
        "security/income_statement_budget_rules.xml",
        "views/income_statement_wizard_views.xml",
        "views/income_statement_budget_views.xml",
        "views/menu_views.xml",
    ],
    "post_init_hook": "income_statement.hooks.post_init_hook",
    "installable": True,
    "application": False,
}
