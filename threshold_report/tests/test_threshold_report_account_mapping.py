from psycopg2.errors import UniqueViolation

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestThresholdReportAccountMapping(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Mapping = cls.env["threshold.report.account.mapping"]
        cls.MappingLine = cls.env["threshold.report.account.mapping.line"]
        cls.account_a = cls.env["account.account"].create({
            "name": "Threshold Mapping Test Account A",
            "code": "THRM.A",
            "account_type": "income",
            "company_id": cls.company.id,
        })

    @mute_logger("odoo.sql_db")
    def test_row_key_unique_per_company(self):
        self.Mapping.create({
            "company_id": self.company.id,
            "row_key": "salary",
        })
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            self.Mapping.create({
                "company_id": self.company.id,
                "row_key": "salary",
            })

    @mute_logger("odoo.sql_db")
    def test_account_unique_per_mapping(self):
        mapping = self.Mapping.create({
            "company_id": self.company.id,
            "row_key": "depreciation",
        })
        self.MappingLine.create({
            "mapping_id": mapping.id,
            "account_id": self.account_a.id,
            "percentage": 100.0,
        })
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            self.MappingLine.create({
                "mapping_id": mapping.id,
                "account_id": self.account_a.id,
                "percentage": 50.0,
            })

    def test_negative_percentage_rejected(self):
        mapping = self.Mapping.create({
            "company_id": self.company.id,
            "row_key": "investor_return",
        })
        with self.assertRaises(ValidationError):
            self.MappingLine.create({
                "mapping_id": mapping.id,
                "account_id": self.account_a.id,
                "percentage": -10.0,
            })

    def test_account_from_another_company_is_allowed(self):
        """A mapping line may point at an account owned by a different,
        unrelated company (e.g. a related company's account), since the
        report intentionally pulls data across company boundaries."""
        other_company = self.env["res.company"].create({
            "name": "Threshold Mapping Test Other Co",
        })
        other_account = self.env["account.account"].create({
            "name": "Threshold Mapping Test Account Other Co",
            "code": "THRM.O",
            "account_type": "income",
            "company_id": other_company.id,
        })
        mapping = self.Mapping.create({
            "company_id": self.company.id,
            "row_key": "debt_retirement",
        })
        line = self.MappingLine.create({
            "mapping_id": mapping.id,
            "account_id": other_account.id,
            "percentage": 100.0,
        })
        self.assertEqual(line.account_id, other_account)
        self.assertNotEqual(line.account_id.company_id, mapping.company_id)
