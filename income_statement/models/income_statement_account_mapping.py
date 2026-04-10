from odoo import fields, models

ROW_KEY_SELECTION = [
    ("sales_revenue", "Sales Revenue"),
    ("cost_purchased_finished_goods", "Cost of Purchased Finished Goods"),
    ("variable_overhead_landed_costs", "Variable Overhead Landed Costs"),
    ("add_back_fixed_overhead", "Add back Fixed Overhead"),
    ("less_variable_operating_expense", "Less Variable Operating Expense"),
    ("interest_expense", "Interest Expense"),
    ("taxes", "Taxes"),
]


class IncomeStatementAccountMapping(models.Model):
    _name = "income.statement.account.mapping"
    _description = "Income Statement Account Mapping"
    _check_company_auto = True

    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    row_key = fields.Selection(
        ROW_KEY_SELECTION,
        string="Row",
        required=True,
    )
    account_ids = fields.Many2many(
        "account.account",
        "income_statement_mapping_account_rel",
        "mapping_id",
        "account_id",
        string="Accounts",
        check_company=True,
    )

    _sql_constraints = [
        (
            "company_row_key_uniq",
            "UNIQUE(company_id, row_key)",
            "Each row type can only have one mapping per company.",
        ),
    ]
