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
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Income Statement Budget"
    _check_company_auto = True

    name = fields.Char(compute="_compute_name", inverse="_inverse_name", store=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )

    @api.model
    def _get_year_selection(self):
        y = fields.Date.today().year
        return [(str(y), str(y))]

    year = fields.Selection(
        selection="_get_year_selection",
        string="Year",
        required=True,
        default=lambda self: str(fields.Date.today().year),
        tracking=True,
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
        tracking=True,
    )
    sales_revenue = fields.Float(required=True, digits=(16, 2), tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        default="draft",
        required=True,
        tracking=True,
    )
    line_ids = fields.One2many(
        "income.statement.budget.line",
        "budget_id",
        string="Budget Lines",
        copy=True,
        check_company=True,
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
        default.setdefault("company_id", self.company_id.id)
        nq, ny = self._next_quarter_and_year()
        today_y = str(fields.Date.today().year)
        if ny != today_y:
            raise ValidationError(
                "Duplicating into year %s is not available when budgets are limited to the current year (%s). "
                "Add a new budget for that year instead."
                % (ny, today_y)
            )
        default["quarter"] = nq
        default["year"] = ny
        dup_domain = [
            ("year", "=", ny),
            ("quarter", "=", nq),
            ("company_id", "=", self.company_id.id),
        ]
        if self.search_count(dup_domain):
            raise ValidationError(
                "Cannot duplicate: company already has a budget for year %s %s."
                % (ny, nq.upper())
            )
        new_budget = super(
            IncomeStatementBudget,
            self.with_context(skip_budget_line_chatter=True),
        ).copy(default)
        new_budget.message_post(
            body="Duplicated from %s." % (self.display_name,),
            subtype_xmlid="mail.mt_note",
        )
        return new_budget

    @api.depends("year", "quarter")
    def _compute_name(self):
        labels = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4"}
        for record in self:
            y = record.year or ""
            q = labels.get(record.quarter, "") if record.quarter else ""
            record.name = "Budget %s %s" % (y, q) if y and q else ""

    def _inverse_name(self):
        pass

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

    @api.constrains("year", "quarter", "company_id")
    def _check_year_quarter_unique(self):
        labels = {"q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4"}
        for record in self:
            if not record.year or not record.quarter or not record.company_id:
                continue
            dup = self.search_count([
                ("year", "=", record.year),
                ("quarter", "=", record.quarter),
                ("company_id", "=", record.company_id.id),
                ("id", "!=", record.id),
            ])
            if dup:
                q = labels.get(record.quarter, record.quarter)
                raise ValidationError(
                    "Year %s already has a budget for %s for this company. "
                    "Each quarter (Q1–Q4) can only be used once per year per company."
                    % (record.year, q)
                )

    def action_confirm(self):
        self.write({"state": "confirmed"})

    def action_draft(self):
        self.write({"state": "draft"})

    def _create_default_budget_lines(self):
        self.ensure_one()
        Line = self.env["income.statement.budget.line"].with_company(self.company_id).with_context(
            skip_budget_line_chatter=True,
        )
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
    _check_company_auto = True

    budget_id = fields.Many2one(
        "income.statement.budget",
        required=True,
        ondelete="cascade",
        check_company=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="budget_id.company_id",
        store=True,
        readonly=True,
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

    def _selection_line_type(self):
        return dict(self._fields["line_type"].selection)

    def _format_money(self, value):
        return "%.2f" % (value or 0.0)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if self.env.context.get("skip_budget_line_chatter"):
            return lines
        sel = self._selection_line_type()
        for line in lines:
            if not line.budget_id:
                continue
            lbl = sel.get(line.line_type, line.line_type)
            line.budget_id.message_post(
                body="Budget line added: %s — %s%% — calculated amount %s"
                % (lbl, line.percentage or 0, self._format_money(line.amount)),
                subtype_xmlid="mail.mt_note",
            )
        return lines

    def write(self, vals):
        track_fields = {"line_type", "percentage", "sequence"}
        interested = track_fields & set(vals)
        snapshots = {}
        if interested and not self.env.context.get("skip_budget_line_chatter"):
            for line in self:
                snapshots[line.id] = {
                    "line_type": line.line_type,
                    "percentage": line.percentage,
                    "sequence": line.sequence,
                    "amount": line.amount,
                }
        res = super().write(vals)
        if snapshots:
            sel = self._selection_line_type()
            for line in self.filtered(lambda l: l.id in snapshots):
                before = snapshots[line.id]
                parts = []
                if "line_type" in vals:
                    o = sel.get(before["line_type"], before["line_type"])
                    n = sel.get(line.line_type, line.line_type)
                    if o != n:
                        parts.append("Line type: %s → %s" % (o, n))
                if "percentage" in vals and before["percentage"] != line.percentage:
                    parts.append(
                        "Percentage: %s%% → %s%%"
                        % (before["percentage"], line.percentage)
                    )
                if "sequence" in vals and before["sequence"] != line.sequence:
                    parts.append(
                        "Sequence: %s → %s" % (before["sequence"], line.sequence)
                    )
                if parts and before["amount"] != line.amount:
                    parts.append(
                        "Calculated amount: %s → %s"
                        % (
                            self._format_money(before["amount"]),
                            self._format_money(line.amount),
                        )
                    )
                if parts:
                    row_lbl = sel.get(line.line_type, line.line_type)
                    line.budget_id.message_post(
                        body="Budget line (%s): %s" % (row_lbl, " | ".join(parts)),
                        subtype_xmlid="mail.mt_note",
                    )
        return res

    def unlink(self):
        if not self.env.context.get("skip_budget_line_chatter"):
            sel = self._selection_line_type()
            for line in self:
                if line.budget_id:
                    lbl = sel.get(line.line_type, line.line_type)
                    line.budget_id.message_post(
                        body="Budget line removed: %s (was %s%%, calculated amount %s)"
                        % (
                            lbl,
                            line.percentage or 0,
                            line._format_money(line.amount),
                        ),
                        subtype_xmlid="mail.mt_note",
                    )
        return super().unlink()

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

