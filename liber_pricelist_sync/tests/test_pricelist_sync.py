# -*- coding: utf-8 -*-

from odoo import fields
from odoo.tests.common import TransactionCase

class TestPricelistSync(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestPricelistSync, cls).setUpClass()
        # Fix legacy NOT NULL constraints if present in database schema
        for table in ['product_template', 'product_product']:
            cls.env.cr.execute(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='{table}' AND column_name='base_unit_count'
            """)
            if cls.env.cr.fetchone():
                cls.env.cr.execute(f"ALTER TABLE {table} ALTER COLUMN base_unit_count DROP NOT NULL;")

    def setUp(self):
        super(TestPricelistSync, self).setUp()
        self.PricelistTier = self.env['pricelist.tier']
        self.ProductPricelist = self.env['product.pricelist']
        self.ProductPricelistItem = self.env['product.pricelist.item']
        self.ProductProduct = self.env['product.product']

        # Create sample Tier
        self.tier_a = self.PricelistTier.create({
            'name': 'Tier A',
            'percentage': 15.0,
            'code': 'TA',
        })

        # Create sample Partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'tier_id': self.tier_a.id,
        })

        # Create isolated test Product
        product_template = self.env['product.template'].create({
            'name': 'Test Pricelist Sync Product Unique',
            'list_price': 20.0,
        })
        self.product_1 = product_template.product_variant_id

        # Create sample Pricelist
        self.pricelist = self.ProductPricelist.create({
            'name': 'Test Pricelist',
            'tier_id': self.tier_a.id,
        })

    def test_01_tier_assignment(self):
        """Test assigning tier to partner and pricelist"""
        self.assertEqual(self.partner.tier_id.name, 'Tier A')
        self.assertEqual(self.pricelist.tier_id.percentage, 15.0)

    def test_02_pricelist_item_calculations(self):
        """Test vendor_cost, percentage_extra, and fixed_price forward and reverse calculations"""
        item = self.ProductPricelistItem.create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product_1.id,
            'compute_price': 'fixed',
            'vendor_cost': 100.0,
            'percentage_extra': 15.0,
        })

        # Forward calculation: 100 + 15% = 115
        self.assertAlmostEqual(item.fixed_price, 115.0, places=2)

        # Reverse calculation when price changes to 138 with 15% extra
        item.write({'fixed_price': 138.0})
        self.assertAlmostEqual(item.vendor_cost, 120.0, places=2)

        # Update percentage extra to 20%
        item.write({'percentage_extra': 20.0})
        self.assertAlmostEqual(item.fixed_price, 144.0, places=2)

    def test_03_tier_change_applies_percentage(self):
        """Test updating tier on pricelist updates item percentage_extra and fixed_price"""
        item = self.ProductPricelistItem.create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product_1.id,
            'compute_price': 'fixed',
            'vendor_cost': 100.0,
            'percentage_extra': 10.0,
            'fixed_price': 110.0,
        })

        tier_b = self.PricelistTier.create({
            'name': 'Tier B',
            'percentage': 25.0,
        })

        self.pricelist.write({'tier_id': tier_b.id})
        self.assertAlmostEqual(item.percentage_extra, 25.0, places=2)
        self.assertAlmostEqual(item.fixed_price, 125.0, places=2)

    def test_04_sync_vendor_prices(self):
        """Test syncing vendor prices for existing pricelist items only"""
        # Create an existing item on the pricelist for product_1
        item_1 = self.ProductPricelistItem.create({
            'pricelist_id': self.pricelist.id,
            'applied_on': '0_product_variant',
            'product_id': self.product_1.id,
            'compute_price': 'fixed',
            'vendor_cost': 50.0,
            'percentage_extra': 15.0,
            'fixed_price': 57.5,
        })

        vendor = self.env['res.partner'].create({'name': 'Test Vendor Sync', 'supplier_rank': 1})
        po = self.env['purchase.order'].create({
            'partner_id': vendor.id,
            'order_line': [(0, 0, {
                'product_id': self.product_1.id,
                'name': self.product_1.name,
                'product_qty': 10,
                'price_unit': 80.0,
                'date_planned': fields.Datetime.now(),
            })],
        })
        po.button_confirm()

        # Create posted vendor bill linked to PO line
        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': vendor.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_1.id,
                'name': self.product_1.name,
                'quantity': 10,
                'price_unit': 80.0,
                'purchase_line_id': po.order_line[0].id,
            })],
        })
        bill.action_post()

        # Execute Sync Vendor Prices on pricelist
        res = self.pricelist.action_sync_vendor_prices()
        self.assertEqual(res['type'], 'ir.actions.client')

        # Verify existing pricelist item vendor_cost was updated to 80.0 and fixed_price to 92.0
        item_1.invalidate_recordset()
        self.assertAlmostEqual(item_1.vendor_cost, 80.0, places=2)
        self.assertAlmostEqual(item_1.percentage_extra, 15.0, places=2)
        self.assertAlmostEqual(item_1.fixed_price, 92.0, places=2)  # 80 * 1.15 = 92
