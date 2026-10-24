# -*- coding: utf-8 -*-

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPricelistSync(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for table in ['product_template', 'product_product']:
            cls.env.cr.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name='base_unit_count'", (table,))
            if cls.env.cr.fetchone():
                cls.env.cr.execute("ALTER TABLE %s ALTER COLUMN base_unit_count DROP NOT NULL" % table)
        cls.tier_a = cls.env['pricelist.tier'].create({'name': 'Tier A', 'percentage': 50.0, 'code': 'TA'})
        cls.partner = cls.env['res.partner'].create({'name': 'Test Customer', 'tier_id': cls.tier_a.id})
        cls.vendor_1 = cls.env['res.partner'].create({'name': 'Vendor One'})
        cls.vendor_2 = cls.env['res.partner'].create({'name': 'Vendor Two (cheaper)'})
        cls.pricelist = cls.env['product.pricelist'].create({'name': 'Website', 'tier_id': cls.tier_a.id})

        def product(name, cost=0.0):
            return cls.env['product.template'].create({'name': name, 'list_price': 1.0, 'standard_price': cost,
                                                      'sale_ok': True, 'purchase_ok': True}).product_variant_id
        cls.p_pricelist = product('P1 vendor price list', cost=10.0)
        cls.p_bill = product('P2 vendor bill', cost=10.0)
        cls.p_avg = product('P3 average cost', cost=40.0)
        cls.p_none = product('P4 no cost')
        # vendor price list: the TOP line wins, not the cheapest
        cls.env['product.supplierinfo'].create([
            {'partner_id': cls.vendor_1.id, 'product_tmpl_id': cls.p_pricelist.product_tmpl_id.id, 'price': 100.0, 'sequence': 1},
            {'partner_id': cls.vendor_2.id, 'product_tmpl_id': cls.p_pricelist.product_tmpl_id.id, 'price': 60.0, 'sequence': 2},
        ])
        # a posted bill for P1 too: the vendor price list must still win; P2 only has the bill
        for prod, price in ((cls.p_pricelist, 80.0), (cls.p_bill, 70.0)):
            bill = cls.env['account.move'].create({
                'move_type': 'in_invoice', 'partner_id': cls.vendor_1.id, 'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {'product_id': prod.id, 'quantity': 1, 'price_unit': price})],
            })
            bill.action_post()

    def test_01_tier_assignment(self):
        self.assertEqual(self.partner.tier_id.name, 'Tier A')
        self.assertEqual(self.pricelist.tier_id.percentage, 50.0)

    def test_02_gross_margin_calculations(self):
        item = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id, 'applied_on': '0_product_variant', 'product_id': self.p_none.id,
            'compute_price': 'fixed', 'vendor_cost': 100.0, 'percentage_extra': 20.0})
        self.assertAlmostEqual(item.fixed_price, 125.0)            # 100 / (1 - 0.20): gross margin, not markup
        item.write({'percentage_extra': 50.0})
        self.assertAlmostEqual(item.fixed_price, 200.0)            # 50% margin doubles the cost
        item.write({'fixed_price': 150.0})
        self.assertAlmostEqual(item.vendor_cost, 75.0)             # 150 * (1 - 0.50)

    def test_03_margin_below_100(self):
        with self.assertRaises(ValidationError):
            self.env['pricelist.tier'].create({'name': 'Bad', 'percentage': 100.0})

    def test_04_cost_priority(self):
        self.assertEqual(self.p_pricelist._liber_vendor_cost(), (100.0, 'vendor_pricelist'))   # top line, not 60
        self.assertEqual(self.p_bill._liber_vendor_cost(), (70.0, 'vendor_bill'))
        self.assertEqual(self.p_avg._liber_vendor_cost(), (40.0, 'average_cost'))
        self.assertEqual(self.p_none._liber_vendor_cost(), (0.0, False))

    def test_05_sync_creates_and_updates(self):
        existing = self.env['product.pricelist.item'].create({
            'pricelist_id': self.pricelist.id, 'applied_on': '0_product_variant', 'product_id': self.p_bill.id,
            'compute_price': 'fixed', 'fixed_price': 5.0, 'percentage_extra': 30.0})
        self.pricelist.action_sync_vendor_prices()
        items = {i.product_id: i for i in self.pricelist.item_ids if i.product_id}
        self.assertAlmostEqual(items[self.p_pricelist].fixed_price, 200.0)      # created: 100 at tier margin 50%
        self.assertEqual(items[self.p_pricelist].cost_source, 'vendor_pricelist')
        self.assertEqual(items[self.p_bill], existing)                           # updated, keeps its own margin
        self.assertAlmostEqual(existing.fixed_price, 100.0)                      # 70 / (1 - 0.30)
        self.assertEqual(existing.cost_source, 'vendor_bill')
        self.assertAlmostEqual(items[self.p_avg].fixed_price, 80.0)             # average cost 40 at 50%
        self.assertNotIn(self.p_none, items)                                     # no cost anywhere: skipped

    def test_06_highest_rule(self):
        # vendor price list 100, last bill 80 -> 100; bill only (P2: 70) -> 70; average cost only -> 40
        self.assertEqual(self.p_pricelist._liber_vendor_cost(rule='highest'), (100.0, 'vendor_pricelist'))
        self.env['product.supplierinfo'].create({'partner_id': self.vendor_1.id, 'product_tmpl_id': self.p_bill.product_tmpl_id.id, 'price': 50.0, 'sequence': 1})
        self.assertEqual(self.p_bill._liber_vendor_cost(rule='highest'), (70.0, 'vendor_bill'))     # bill 70 > list 50
        self.assertEqual(self.p_bill._liber_vendor_cost(), (50.0, 'vendor_pricelist'))             # default rule: list first
        self.assertEqual(self.p_avg._liber_vendor_cost(rule='highest'), (40.0, 'average_cost'))

    def test_07_sync_lists_skipped_products(self):
        res = self.pricelist.action_sync_vendor_prices()
        self.assertIn('Skipped:', res['params']['message'])
        self.assertIn('P4 no cost', res['params']['message'])

    def test_08_preferred_vendor_and_same_result_for_every_user(self):
        lines = self.p_pricelist.product_tmpl_id.seller_ids.sorted(lambda l: l.sequence)
        self.assertEqual(self.p_pricelist._liber_vendor_cost(), (100.0, 'vendor_pricelist'))
        lines[1].x_preferred = True                       # Dale marks the cheaper vendor as preferred
        self.assertEqual(self.p_pricelist._liber_vendor_cost(), (60.0, 'vendor_pricelist'))
        # a user restricted to another company gets the same answer (the line is read with full rights)
        other = self.env['res.company'].create({'name': 'Other Co'})
        user = self.env['res.users'].create({'name': 'Liz', 'login': 'liz_t', 'company_id': other.id, 'company_ids': [(6, 0, [other.id, self.env.company.id])],
                                             'groups_id': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.assertEqual(self.p_pricelist.with_user(user)._liber_vendor_cost(self.env.company), (60.0, 'vendor_pricelist'))
        self.pricelist.action_sync_vendor_prices()
        item = self.pricelist.item_ids.filtered(lambda i: i.product_id == self.p_pricelist)
        self.assertEqual(item.cost_vendor_id, self.vendor_2)
