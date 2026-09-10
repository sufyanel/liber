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
            wizard._get_mapping_amount_or_default("savings", wizard.savings), 12345.0
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
            wizard._get_mapping_amount_or_default("savings", wizard.savings), 0.0
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
