from odoo import api, SUPERUSER_ID

ACCOUNT_CODE_DEFAULTS = {
    "sales_revenue": [
        "04.1.101", "04.1.102", "04.1.104",
    ],
    "cost_purchased_finished_goods": [
        "05.1.101", "05.1.102", "05.1.103", "05.1.104", "05.1.105",
        "05.2.101", "05.2.102", "05.1.1.104", "500000",
    ],
    "variable_overhead_landed_costs": [
        "05.1.113", "06.1.302", "05.1.106", "220110", "06.1.304", "220100",
    ],
    "add_back_fixed_overhead": [
        "01.1.116", "230200", "06.2.505", "06.2.604",
        "220601", "06.2.605", "220600", "220900", "06.2.613",
    ],
    "less_variable_operating_expense": [
        "06.2.611", "240101", "06.2.201", "212300", "06.2.503", "620000",
    ],
    "interest_expense": ["06.2.203"],
    "taxes": ["230150"],
}


def post_init_hook(cr, registry):
    cr.execute(
        """
        UPDATE income_statement_budget
        SET company_id = (SELECT id FROM res_company ORDER BY id LIMIT 1)
        WHERE company_id IS NULL
        """
    )
    env = api.Environment(cr, SUPERUSER_ID, {})
    _seed_default_mappings(env)


def _seed_default_mappings(env):
    Mapping = env["income.statement.account.mapping"]
    Account = env["account.account"]
    companies = env["res.company"].search([])
    for company in companies:
        for row_key, codes in ACCOUNT_CODE_DEFAULTS.items():
            existing = Mapping.search([
                ("company_id", "=", company.id),
                ("row_key", "=", row_key),
            ], limit=1)
            if existing:
                continue
            accounts = Account.search([
                ("company_id", "=", company.id),
                ("code", "in", codes),
            ])
            if accounts:
                Mapping.create({
                    "company_id": company.id,
                    "row_key": row_key,
                    "account_ids": [(6, 0, accounts.ids)],
                })
