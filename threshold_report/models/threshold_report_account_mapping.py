from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

ROW_KEY_SELECTION = [
    ("salary", "Salary"),
    ("depreciation", "Depreciation"),
    ("change_ar", "Change in Accounts Receivable"),
    ("change_payables", "Change in Accounts Payable"),
    ("change_inventory", "Change in Inventory"),
    ("debt_retirement", "Debt Retirement - Principal Only"),
    ("investor_return", "Investor Return (Equity or Dividend)"),
    ("capital_investments", "Capital Investments"),
    ("savings", "Savings"),
    ("taxes", "Taxes"),
]


class ThresholdReportAccountMapping(models.Model):
    _name = "threshold.report.account.mapping"
    _description = "Threshold Report Account Mapping"
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
    amount = fields.Float(
        string="Manual Amount",
        digits=(16, 2),
        help="Used only when this row has no account lines. "
        "Ignored as soon as at least one account line is added.",
    )
    line_ids = fields.One2many(
        "threshold.report.account.mapping.line",
        "mapping_id",
        string="Account Lines",
        copy=True,
        check_company=True,
    )

    _sql_constraints = [
        (
            "company_row_key_uniq",
            "UNIQUE(company_id, row_key)",
            "Each row type can only have one mapping per company.",
        ),
    ]


class ThresholdReportAccountMappingLine(models.Model):
    _name = "threshold.report.account.mapping.line"
    _description = "Threshold Report Account Mapping Line"
    _check_company_auto = True

    mapping_id = fields.Many2one(
        "threshold.report.account.mapping",
        required=True,
        ondelete="cascade",
        check_company=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="mapping_id.company_id",
        store=True,
        readonly=True,
    )
    account_id = fields.Many2one(
        "account.account",
        string="Account",
        required=True,
        help="Any company's account can be used here — the report pulls "
        "data straight from this account regardless of which company owns "
        "it, e.g. to attribute a related company's account to this row.",
    )
    percentage = fields.Float(
        string="Percentage",
        default=100.0,
        digits=(16, 2),
    )

    _sql_constraints = [
        (
            "mapping_account_uniq",
            "UNIQUE(mapping_id, account_id)",
            "An account can only appear once per mapping row.",
        ),
    ]

    @api.constrains("percentage")
    def _check_percentage(self):
        for line in self:
            if line.percentage < 0:
                raise ValidationError(_("Percentage cannot be negative."))
