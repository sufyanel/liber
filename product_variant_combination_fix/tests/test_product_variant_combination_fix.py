# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestProductVariantCombinationFix(TransactionCase):
    """See models/product_template.py: repairs a variant whose combination
    incorrectly includes 'no_variant' attribute values, which stops it from
    being matched (and reused) by new sale/purchase orders and leads to a
    duplicate variant being created instead.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.color_attribute = cls.env['product.attribute'].create({
            'name': 'Test Color',
            'create_variant': 'always',
            'value_ids': [
                (0, 0, {'name': 'Red'}),
                (0, 0, {'name': 'Blue'}),
            ],
        })
        cls.spec_attribute = cls.env['product.attribute'].create({
            'name': 'Test Spec',
            'create_variant': 'no_variant',
            'value_ids': [(0, 0, {'name': '1.0'})],
        })
        cls.template = cls.env['product.template'].create({
            'name': 'M10-025',
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': cls.color_attribute.id,
                    'value_ids': [(6, 0, cls.color_attribute.value_ids.ids)],
                }),
                (0, 0, {
                    'attribute_id': cls.spec_attribute.id,
                    'value_ids': [(6, 0, cls.spec_attribute.value_ids.ids)],
                }),
            ],
        })
        cls.red_ptav = cls.template.attribute_line_ids.filtered(
            lambda line: line.attribute_id == cls.color_attribute
        ).product_template_value_ids.filtered(lambda v: v.name == 'Red')
        cls.spec_ptav = cls.template.attribute_line_ids.filtered(
            lambda line: line.attribute_id == cls.spec_attribute
        ).product_template_value_ids
        # Odoo already created one clean variant per color (Red/Blue), each
        # *without* the no_variant spec value, exactly like a correctly
        # created variant should look.
        cls.red_variant = cls.template.product_variant_ids.filtered(
            lambda p: cls.red_ptav <= p.product_template_attribute_value_ids
        )

    def _pollute_red_variant(self):
        """Simulate the historical corruption: link the no_variant spec
        value directly onto the Red variant, the way old data apparently
        got created."""
        self.red_variant.product_template_attribute_value_ids = [(4, self.spec_ptav.id)]

    def test_strips_stale_link_when_no_duplicate_exists(self):
        self._pollute_red_variant()
        self.assertIn(self.spec_ptav, self.red_variant.product_template_attribute_value_ids)

        self.template._fix_polluted_variant_combinations()

        self.assertEqual(
            self.red_variant.product_template_attribute_value_ids, self.red_ptav,
            "the no_variant spec value should have been unlinked from the variant",
        )

    def test_merges_duplicate_created_for_the_clean_combination(self):
        self._pollute_red_variant()
        # This is what happened in production: a new, clean variant for the
        # same real combination got created because the polluted one could
        # no longer be matched.
        duplicate_variant = self.env['product.product'].create({
            'product_tmpl_id': self.template.id,
            'product_template_attribute_value_ids': [(6, 0, self.red_ptav.ids)],
        })
        # Only sale/purchase are this module's actual dependencies, and an
        # order header can carry extra required fields from whichever other
        # apps (stock, accounting, ...) happen to be installed alongside
        # them. Attach the test lines to an existing order rather than
        # constructing a new header, so this doesn't need to know about any
        # of that - only sale.order.line/purchase.order.line, which this
        # module actually writes to, are exercised directly.
        order = self.env['sale.order'].search([('state', 'in', ('draft', 'sent'))], limit=1)
        sale_line = self.env['sale.order.line'].create({
            'order_id': order.id,
            'product_id': duplicate_variant.id,
            'product_uom_qty': 1,
            'name': duplicate_variant.display_name,
        })

        purchase_order = self.env['purchase.order'].search([('state', '=', 'draft')], limit=1)
        purchase_line = self.env['purchase.order.line'].create({
            'order_id': purchase_order.id,
            'product_id': duplicate_variant.id,
            'product_qty': 1,
            'product_uom': duplicate_variant.uom_po_id.id,
            'name': duplicate_variant.display_name,
            'date_planned': order.date_order,
            'price_unit': 0,
        })

        self.template._fix_polluted_variant_combinations()

        self.assertFalse(duplicate_variant.exists(), "the duplicate variant should have been deleted")
        self.assertEqual(sale_line.product_id, self.red_variant, "the sale line should now point to the kept variant")
        self.assertEqual(
            purchase_line.product_id, self.red_variant,
            "the purchase line should now point to the kept variant",
        )
        self.assertEqual(
            self.red_variant.product_template_attribute_value_ids, self.red_ptav,
            "the no_variant spec value should have been unlinked from the kept variant",
        )

    def test_cron_auto_discovers_polluted_templates(self):
        self._pollute_red_variant()

        self.env['product.template']._cron_fix_polluted_variant_combinations()

        self.assertEqual(
            self.red_variant.product_template_attribute_value_ids, self.red_ptav,
            "the scheduled action should have found the polluted template on its own and fixed it",
        )

    def test_cron_is_a_noop_when_nothing_is_polluted(self):
        # self.template is untouched here (no pollution introduced), so this
        # only proves the scan doesn't fail or change anything when there is
        # nothing to fix for it - other, genuinely dirty templates that may
        # already exist in the database are exercised by the test above.
        before = self.red_variant.product_template_attribute_value_ids

        self.template._fix_polluted_variant_combinations()

        self.assertEqual(self.red_variant.product_template_attribute_value_ids, before)
