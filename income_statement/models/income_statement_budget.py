from collections import Counter

from odoo import api, fields, models
from odoo.exceptions import ValidationError

BUDGET_LINE_TYPE_ORDER = [
    "cost_purchased_finished_goods",
    "variable_overhead_landed_costs",
    "add_back_fixed_overhead",
    "less_variable_operating_expense",
    "selling_general_administrative",
    "total_operating_expenses",
    "interest_expense",
    "taxes",
]


class IncomeStatementBudget(models.Model):
    _name = "income.statement.budget"
    _description = "Income Statement Budget"

    name = fields.Char(compute="_compute_name", store=True, readonly=True)

    @api.model
    def _get_year_selection(self):
        y = fields.Date.today().year
        return [(str(yyyy), str(yyyy)) for yyyy in range(y, y + 5)]

    year = fields.Selection(
        selection="_get_year_selection",
        string="Year",
        readonely=True,
        store=True,
        required=True,
        default=lambda self: str(fields.Date.today().year),
    )
    quarter = fields.Selection(
        [
            ("q1", "Q1"),
            ("q2", "Q2"),
            ("q3", "Q3"),
            ("q4", "Q4"),
        ],
        string="Quarter",
        required=True,
        default="q1",
    )
    sales_revenue = fields.Float(required=True, digits=(16, 2))
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        default="draft",
        required=True,
    )
    line_ids = fields.One2many(
        "income.statement.budget.line",
        "budget_id",
        string="Budget Lines",
        copy=True,
    )

    def _next_quarter_and_year(self):
        self.ensure_one()
        order = ("q1", "q2", "q3", "q4")
        if self.quarter not in order:
            return "q2", self.year
        i = order.index(self.quarter)
        if i < 3:
            return order[i + 1], self.year
        y = int(self.year) if self.year and str(self.year).isdigit() else fields.Date.today().year
        return "q1", str(y + 1)

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.setdefault("state", "draft")
        nq, ny = self._next_quarter_and_year()
        default["quarter"] = nq
        default["year"] = ny
        return super().copy(default)

    @api.depends("year", "quarter")
    def _compute_name(self):
        labels = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4"}
        for record in self:
            y = record.year or ""
            q = labels.get(record.quarter, "") if record.quarter else ""
            record.name = "Budget %s %s" % (y, q) if y and q else ""

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.line_ids:
                record._create_default_budget_lines()
        for record, vals in zip(records, vals_list):
            if vals.get("state") == "confirmed":
                record._check_confirmable(vals)
        return records

    def write(self, vals):
        if vals.get("state") == "confirmed":
            self._check_confirmable(vals)
        return super().write(vals)

    def _check_confirmable(self, vals=None):
        vals = vals or {}
        for record in self:
            revenue = vals.get("sales_revenue", record.sales_revenue)
            if (revenue or 0) <= 0:
                raise ValidationError(
                    "Cannot confirm a budget with zero sales revenue."
                )
            if not record.line_ids:
                raise ValidationError(
                    "Cannot confirm a budget with no budget lines."
                )
            if not any((l.percentage or 0) != 0 for l in record.line_ids):
                raise ValidationError(
                    "Cannot confirm a budget when all budget lines have zero percent "
                    "and calculated amounts are all zero."
                )

    @api.constrains("year", "quarter")
    def _check_year_quarter_unique(self):
        labels = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4"}
        for record in self:
            if not record.year or not record.quarter:
                continue
            dup = self.search_count([
                ("year", "=", record.year),
                ("quarter", "=", record.quarter),
                ("id", "!=", record.id),
            ])
            if dup:
                q = labels.get(record.quarter, record.quarter)
                raise ValidationError(
                    "Year %s already has a budget for %s. "
                    "Each quarter (Q1–Q4) can only be used once per year."
                    % (record.year, q)
                )

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_draft(self):
        self.write({"state": "draft"})

    def _create_default_budget_lines(self):
        self.ensure_one()
        Line = self.env["income.statement.budget.line"]
        for sequence, line_type in enumerate(BUDGET_LINE_TYPE_ORDER, start=1):
            Line.create({
                "budget_id": self.id,
                "sequence": sequence * 10,
                "line_type": line_type,
                "percentage": 0,
            })


class IncomeStatementBudgetLine(models.Model):
    _name = "income.statement.budget.line"
    _description = "Income Statement Budget Line"
    _order = "sequence, id"

    budget_id = fields.Many2one(
        "income.statement.budget",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    line_type = fields.Selection(
        [
            ("cost_purchased_finished_goods", "Cost of Purchased Finished Goods"),
            ("variable_overhead_landed_costs", "Variable Overhead Landed Costs"),
            ("add_back_fixed_overhead", "Add back Fixed Overhead"),
            ("less_variable_operating_expense", "Less Variable Operating Expense (xxx)"),
            ("selling_general_administrative", "Selling, General & Administrative"),
            ("total_operating_expenses", "Total Operating Expenses"),
            ("interest_expense", "Interest expense (xxx)"),
            ("taxes", "Taxes (xxx)"),
        ],
        required=True,
    )
    percentage = fields.Integer(
        string="Percentage",
        default=0,
    )
    amount = fields.Float(
        string="Calculated Amount",
        compute="_compute_amount",
        digits=(16, 2),
        store=True,
    )

    @api.depends("percentage", "budget_id.sales_revenue")
    def _compute_amount(self):
        for line in self:
            revenue = line.budget_id.sales_revenue or 0.0
            pct = line.percentage or 0
            line.amount = revenue * pct / 100.0

    @api.constrains("budget_id", "line_type")
    def _check_line_type_unique_per_budget(self):
        labels = dict(self.fields_get(["line_type"])["line_type"]["selection"])
        for budget in self.mapped("budget_id"):
            if not budget:
                continue
            line_types = [l.line_type for l in budget.line_ids if l.line_type]
            if len(line_types) == len(set(line_types)):
                continue
            dup_keys = [k for k, c in Counter(line_types).items() if c > 1]
            dup_names = [labels.get(k, k) for k in dup_keys]
            raise ValidationError(
                "Each line type can only appear once per budget. "
                "Duplicated line types: %s." % ", ".join(dup_names)
            )

    @api.constrains("percentage", "budget_id")
    def _check_percentage_sum_max(self):
        for budget in self.mapped("budget_id"):
            if not budget:
                continue
            total = sum((l.percentage or 0) for l in budget.line_ids)
            if total > 100:
                raise ValidationError(
                    "The sum of percentages on all budget lines cannot exceed "
                    "100%% (current total: %s%%)." % total
                )
