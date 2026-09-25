from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestVariantMatching(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PA = cls.env['product.attribute']
        cls.brand = PA.create({'name': 'Brand LVM', 'create_variant': 'dynamic',
                               'value_ids': [(0, 0, {'name': 'Raymond'}), (0, 0, {'name': 'Bordignon Springs'})]})
        cls.spec = PA.create({'name': 'Spec LVM', 'create_variant': 'no_variant', 'value_ids': [(0, 0, {'name': '3/4'})]})
        cls.tmpl = cls.env['product.template'].create({'name': 'M07-035 LVM', 'attribute_line_ids': [
            (0, 0, {'attribute_id': a.id, 'value_ids': [(6, 0, a.value_ids.ids)]}) for a in (cls.brand, cls.spec)]})
        ptavs = cls.tmpl.attribute_line_ids.product_template_value_ids
        cls.raymond = ptavs.filtered(lambda p: p.name != 'Bordignon Springs')
        cls.bordignon = ptavs.filtered(lambda p: p.name != 'Raymond')
        # stocked part imported with the 'Never' spec value on it
        cls.real = cls.env['product.product'].create({'product_tmpl_id': cls.tmpl.id, 'default_code': '3/4 X 3 1/2 M-6',
                                                      'product_template_attribute_value_ids': [(6, 0, cls.raymond.ids)]})

    def test_order_uses_real_part(self):
        self.assertEqual(self.tmpl._create_product_variant(self.raymond), self.real)
        self.assertEqual(len(self.tmpl.product_variant_ids), 1, 'no empty duplicate is created')

    def test_other_brand_still_created(self):
        bor = self.tmpl._create_product_variant(self.bordignon)
        self.assertTrue(bor and bor != self.real)

    def test_archived_real_part_is_reactivated(self):
        self.real.active = False
        self.assertEqual(self.tmpl._create_product_variant(self.raymond), self.real)
        self.assertTrue(self.real.active)

    def test_other_brand_copies_are_reused_not_multiplied(self):
        # Bordignon row imported with the 'Never' value: an exact match never exists
        bor_copy = self.env['product.product'].create({'product_tmpl_id': self.tmpl.id,
                                                       'product_template_attribute_value_ids': [(6, 0, self.bordignon.ids)]})
        first = self.tmpl._create_product_variant(self.bordignon)
        second = self.tmpl._create_product_variant(self.bordignon)
        self.assertEqual(first, bor_copy)
        self.assertEqual(second, bor_copy)
        self.assertEqual(len(self.tmpl.product_variant_ids), 2, 'no new Bordignon copy')
