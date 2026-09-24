from datetime import date

from odoo.tests.common import TransactionCase


class TestThresholdReportWizardMapping(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A dedicated, lock-free company: posting test entries into past
        # periods must not depend on whichever fiscal/tax lock dates happen
        # to be set on the database's real default company.
        cls.company = cls.env["res.company"].create({
            "name": "Threshold Report Test Co",
        })
        cls.account_a = cls.env["account.account"].create({
            "name": "Threshold Wizard Test Income",
            "code": "THRW.A",
            "account_type": "income",
            "company_id": cls.company.id,
        })
        cls.counter_account = cls.env["account.account"].create({
            "name": "Threshold Wizard Test Counter",
            "code": "THRW.C",
            "account_type": "asset_current",
            "company_id": cls.company.id,
        })
        cls.journal = cls.env["account.journal"].create({
            "name": "Threshold Test Journal",
            "code": "THRJ",
            "type": "general",
            "company_id": cls.company.id,
        })

    def _post_move(self, amount, move_date):
        debit_amount = amount if amount > 0 else 0.0
        credit_amount = -amount if amount < 0 else 0.0
        move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.journal.id,
            "date": move_date,
            "line_ids": [
                (0, 0, {
                    "account_id": self.account_a.id,
                    "debit": debit_amount,
                    "credit": credit_amount,
                }),
                (0, 0, {
                    "account_id": self.counter_account.id,
                    "debit": credit_amount,
                    "credit": debit_amount,
                }),
            ],
        })
        move.action_post()
        return move

    def _make_wizard(self):
        return self.env["threshold.report.wizard"].create({
            "company_id": self.company.id,
            "duration": "year",
            "year": "2024",
        })

    def test_mapping_amount_computed_from_weighted_account_lines(self):
        self._post_move(1000.0, date(2024, 6, 15))
        mapping = self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "salary",
        })
        self.env["threshold.report.account.mapping.line"].create({
            "mapping_id": mapping.id,
            "account_id": self.account_a.id,
            "percentage": 50.0,
        })
        wizard = self._make_wizard()
        self.assertAlmostEqual(wizard._get_mapping_amount("salary"), 500.0)

    def test_mapping_amount_falls_back_to_manual_amount_without_lines(self):
        self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "depreciation",
            "amount": 750.0,
        })
        wizard = self._make_wizard()
        self.assertAlmostEqual(wizard._get_mapping_amount("depreciation"), 750.0)

    def test_mapping_amount_without_mapping_is_zero(self):
        wizard = self._make_wizard()
        self.assertEqual(wizard._get_mapping_amount("investor_return"), 0.0)

    def test_mapping_lines_take_precedence_over_amount(self):
        self._post_move(1000.0, date(2024, 6, 15))
        mapping = self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "salary",
            "amount": 999999.0,
        })
        self.env["threshold.report.account.mapping.line"].create({
            "mapping_id": mapping.id,
            "account_id": self.account_a.id,
            "percentage": 100.0,
        })
        wizard = self._make_wizard()
        self.assertAlmostEqual(wizard._get_mapping_amount("salary"), 1000.0)

    def test_mapping_balance_change_only_counts_the_period_delta(self):
        self._post_move(400.0, date(2023, 3, 1))  # before the period: opening balance
        self._post_move(600.0, date(2024, 5, 1))  # inside the period: adds to closing balance
        mapping = self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "change_ar",
        })
        self.env["threshold.report.account.mapping.line"].create({
            "mapping_id": mapping.id,
            "account_id": self.account_a.id,
            "percentage": 100.0,
        })
        wizard = self._make_wizard()
        self.assertAlmostEqual(wizard._get_mapping_balance_change("change_ar"), 600.0)

    def test_manual_field_falls_back_to_wizard_value_without_mapping(self):
        wizard = self._make_wizard()
        wizard.savings = 12345.0
        self.assertAlmostEqual(
            wizard._get_mapping_value("savings", default=wizard.savings), 12345.0
        )

    def test_manual_field_uses_mapping_when_configured_even_if_zero(self):
        # A configured mapping is authoritative, even though it computes to
        # 0.0 here (no lines, no manual amount set) - it must NOT fall back
        # to the wizard's own field in that case.
        self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "savings",
        })
        wizard = self._make_wizard()
        wizard.savings = 12345.0
        self.assertEqual(
            wizard._get_mapping_value("savings", default=wizard.savings), 0.0
        )

    def test_mapping_value_uses_point_balance_by_default(self):
        """use_balance_change defaults to False, so _get_mapping_value must
        behave exactly like _get_mapping_amount: the balance posted during
        the period, ignoring what happened before it."""
        self._post_move(400.0, date(2023, 3, 1))  # before the period
        self._post_move(600.0, date(2024, 5, 1))  # inside the period
        mapping = self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "salary",
        })
        self.env["threshold.report.account.mapping.line"].create({
            "mapping_id": mapping.id,
            "account_id": self.account_a.id,
            "percentage": 100.0,
        })
        wizard = self._make_wizard()
        self.assertFalse(mapping.use_balance_change)
        self.assertAlmostEqual(wizard._get_mapping_value("salary"), 600.0)

    def test_mapping_value_uses_period_change_when_enabled(self):
        """With Use Period Change on, _get_mapping_value must switch to the
        closing-minus-opening balance for ANY row key, not just Change in
        A/R and Change in Inventory."""
        self._post_move(400.0, date(2023, 3, 1))  # before the period: opening balance
        self._post_move(600.0, date(2024, 5, 1))  # inside the period: adds to closing balance
        mapping = self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "salary",
            "use_balance_change": True,
        })
        self.env["threshold.report.account.mapping.line"].create({
            "mapping_id": mapping.id,
            "account_id": self.account_a.id,
            "percentage": 100.0,
        })
        wizard = self._make_wizard()
        self.assertAlmostEqual(wizard._get_mapping_value("salary"), 600.0)
        self.assertAlmostEqual(
            wizard._get_mapping_balance_change("salary"), 600.0,
            msg="closing (1000) minus opening (400) is the period change",
        )

    def test_threshold_data_uses_mapping_for_taxes_and_capital_investments(self):
        self._post_move(2000.0, date(2024, 3, 1))
        taxes_mapping = self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "taxes",
            "amount": 800.0,
        })
        self.assertTrue(taxes_mapping)
        capital_mapping = self.env["threshold.report.account.mapping"].create({
            "company_id": self.company.id,
            "row_key": "capital_investments",
        })
        self.env["threshold.report.account.mapping.line"].create({
            "mapping_id": capital_mapping.id,
            "account_id": self.account_a.id,
            "percentage": 100.0,
        })
        wizard = self._make_wizard()
        wizard.tax = 999.0
        wizard.capital_investments = 111.0
        wizard.savings = 222.0
        data = wizard._get_threshold_data()
        self.assertAlmostEqual(data["taxes"], 800.0)
        self.assertAlmostEqual(data["capital_investments"], 2000.0)
        # savings has no mapping configured, so the wizard's manual field is used
        self.assertAlmostEqual(data["savings"], 222.0)


class TestThresholdReportWizardPayablesChange(TransactionCase):
    """Change in Accounts Payable must diff the amount owed at the period's
    opening and closing dates, not sum today's live bill.amount_residual -
    which goes wrong for any bill that has since been paid off."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create({
            "name": "Threshold Payables Test Co",
        })
        cls.vendor = cls.env["res.partner"].create({
            "name": "Threshold Payables Test Vendor",
        })
        cls.product = cls.env["product.product"].create({
            "name": "Threshold Payables Test Service",
            "detailed_type": "service",
            "purchase_ok": True,
        })
        cls.payable_account = cls.env["account.account"].create({
            "name": "Threshold Payables Test AP",
            "code": "THRP.AP",
            "account_type": "liability_payable",
            "reconcile": True,
            "company_id": cls.company.id,
        })
        cls.expense_account = cls.env["account.account"].create({
            "name": "Threshold Payables Test Expense",
            "code": "THRP.EXP",
            "account_type": "expense",
            "company_id": cls.company.id,
        })
        cls.bank_account = cls.env["account.account"].create({
            "name": "Threshold Payables Test Bank",
            "code": "THRP.BANK",
            "account_type": "asset_cash",
            "company_id": cls.company.id,
        })
        cls.purchase_journal = cls.env["account.journal"].create({
            "name": "Threshold Payables Test Purchase Journal",
            "code": "THRPJ",
            "type": "purchase",
            "company_id": cls.company.id,
        })
        cls.bank_journal = cls.env["account.journal"].create({
            "name": "Threshold Payables Test Bank Journal",
            "code": "THRBJ",
            "type": "general",
            "company_id": cls.company.id,
        })
        cls.mapping = cls.env["threshold.report.account.mapping"].create({
            "company_id": cls.company.id,
            "row_key": "change_payables",
        })
        cls.env["threshold.report.account.mapping.line"].create({
            "mapping_id": cls.mapping.id,
            "account_id": cls.payable_account.id,
            "percentage": 100.0,
        })

    def _make_wizard(self, duration="quarter", year="2024", quarter="Q1"):
        return self.env["threshold.report.wizard"].create({
            "company_id": self.company.id,
            "duration": duration,
            "year": year,
            "quarter": quarter,
        })

    def _create_bill(self, bill_date, amount):
        po = self.env["purchase.order"].create({
            "partner_id": self.vendor.id,
            "company_id": self.company.id,
            "dest_address_id": self.company.partner_id.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "name": "Threshold Payables Test Line",
                "product_qty": 1,
                "price_unit": amount,
            })],
        })
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.vendor.id,
            "company_id": self.company.id,
            "journal_id": self.purchase_journal.id,
            "invoice_date": bill_date,
            "date": bill_date,
            "line_ids": [
                (0, 0, {
                    "account_id": self.expense_account.id,
                    "name": "Threshold Payables Test Expense Line",
                    "quantity": 1,
                    "price_unit": amount,
                    "debit": amount,
                    "credit": 0.0,
                    "purchase_line_id": po.order_line.id,
                }),
                (0, 0, {
                    "account_id": self.payable_account.id,
                    "name": "Threshold Payables Test Payable Line",
                    "partner_id": self.vendor.id,
                    "debit": 0.0,
                    "credit": amount,
                }),
            ],
        })
        bill.action_post()
        return bill

    def _pay_bill(self, bill, amount, pay_date):
        payable_line = bill.line_ids.filtered(lambda l: l.account_id == self.payable_account)
        payment_move = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.bank_journal.id,
            "date": pay_date,
            "line_ids": [
                (0, 0, {
                    "account_id": self.payable_account.id,
                    "partner_id": self.vendor.id,
                    "debit": amount,
                    "credit": 0.0,
                }),
                (0, 0, {
                    "account_id": self.bank_account.id,
                    "debit": 0.0,
                    "credit": amount,
                }),
            ],
        })
        payment_move.action_post()
        payment_payable_line = payment_move.line_ids.filtered(lambda l: l.account_id == self.payable_account)
        (payable_line + payment_payable_line).reconcile()

    def test_change_payables_uses_period_boundaries_not_live_residual(self):
        """A bill posted inside the period but only paid off after the
        period's end must still show as owed at the period's end date, even
        though its live amount_residual is 0 by the time the report runs."""
        bill = self._create_bill(date(2024, 1, 10), 5000.0)
        self._pay_bill(bill, 5000.0, date(2024, 6, 1))  # settled after the Q1 period ends

        # By the time the test (and a real report) runs, the bill looks fully paid.
        self.assertTrue(self.company.currency_id.is_zero(bill.amount_residual))

        wizard = self._make_wizard()
        self.assertAlmostEqual(
            wizard._get_mapping_payables_amount("change_payables"), 5000.0,
            msg="unpaid at both Jan 1 (opening=0, bill didn't exist yet) and "
                "Mar 31 (closing=5000, still unpaid then) -> change = 5000",
        )

    def test_change_payables_negative_when_paid_within_period(self):
        """A bill posted before the period and fully paid inside it must
        show a negative change: it was owed at the opening date and is not
        owed by the closing date."""
        bill = self._create_bill(date(2023, 11, 1), 1000.0)
        self._pay_bill(bill, 1000.0, date(2024, 2, 15))  # paid inside Q1 2024

        wizard = self._make_wizard()
        self.assertAlmostEqual(
            wizard._get_mapping_payables_amount("change_payables"), -1000.0,
            msg="owed (1000) at Jan 1 opening, paid off by Mar 31 closing (0) -> change = -1000",
        )
