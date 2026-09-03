# -*- coding: utf-8 -*-
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _cron_fix_polluted_variant_combinations(self):
        """Entry point for the manually-triggered scheduled action.

        Finds every product template that actually has this corruption - at
        least one variant whose combination includes a value from a
        'no_variant' attribute - and fixes all of them in one pass, so this
        doesn't need a maintained list of affected products or a recurring
        run. See `_fix_polluted_variant_combinations` for what "fixes" means.
        """
        polluted_variants = self.env['product.product'].with_context(active_test=False).search([
            ('product_template_attribute_value_ids.attribute_id.create_variant', '=', 'no_variant'),
        ])
        templates = polluted_variants.product_tmpl_id
        if not templates:
            _logger.info("No polluted variant combination found, nothing to fix.")
            return
        _logger.info(
            "Found %s product template(s) with a polluted variant combination.", len(templates),
        )
        for template in templates:
            try:
                with self.env.cr.savepoint():
                    template._fix_polluted_variant_combinations()
            except Exception:
                _logger.exception(
                    "Failed to fix variant combinations for template %s (%s) - left untouched, "
                    "please review it manually.", template.id, template.display_name,
                )

    def _fix_polluted_variant_combinations(self):
        """Repair variants whose combination incorrectly includes values
        from 'no_variant' attributes.

        A variant's defining combination must only contain values from
        'always'/'dynamic' attributes (see `_create_product_variant` and
        `_without_no_variant_attributes` on `product.template.attribute.
        value`). When it also carries 'no_variant' values, the stored
        `combination_indices` never matches the combination a new sale or
        purchase order computes for the same real product, so Odoo creates
        a brand new duplicate variant instead of reusing this one.

        For each set of variants that share the same "clean" (no_variant
        values excluded) combination:
        - if more than one variant exists, the oldest is kept (it is the
          one with sales/purchase/stock history), sale and purchase order
          lines pointing to the other(s) are moved onto it, and the other(s)
          are deleted;
        - the stale no_variant links are stripped from the kept variant so
          its `combination_indices` matches what future orders will look up.
        """
        self.ensure_one()
        variants = self.with_context(active_test=False).product_variant_ids.sorted('create_date')
        if len(variants) < 2:
            return

        groups = {}
        for variant in variants:
            key = tuple(sorted(
                variant.product_template_attribute_value_ids._without_no_variant_attributes().ids
            ))
            groups[key] = groups.get(key, self.env['product.product']) | variant

        for group in groups.values():
            keep, duplicates = group[0], group[1:]
            for duplicate in duplicates:
                self._merge_duplicate_variant(keep, duplicate)
            stale = keep.product_template_attribute_value_ids - \
                keep.product_template_attribute_value_ids._without_no_variant_attributes()
            if stale:
                _logger.info(
                    "Stripping %s stale no_variant attribute value(s) from variant %s (%s)",
                    len(stale), keep.id, keep.display_name,
                )
                keep.product_template_attribute_value_ids = [(3, value.id) for value in stale]

    def _merge_duplicate_variant(self, keep, duplicate):
        """Move sale/purchase order lines from `duplicate` onto `keep`, then
        delete `duplicate`.

        Left in place (with a warning logged) if the order lines can't be
        moved (e.g. the sale order is locked/invoiced/delivered) or if
        anything else still references it (stock/accounting) - either case
        needs a manual look, and must not abort fixing other variants or
        other products.
        """
        try:
            with self.env.cr.savepoint():
                self.env['sale.order.line'].search([
                    ('product_id', '=', duplicate.id),
                ]).write({'product_id': keep.id})
                self.env['purchase.order.line'].search([
                    ('product_id', '=', duplicate.id),
                ]).write({'product_id': keep.id})
        except Exception:
            _logger.warning(
                "Could not move sale/purchase order lines off variant %s (template %s) onto %s "
                "(order likely locked/invoiced/delivered) - left in place, please review it "
                "manually.", duplicate.id, self.display_name, keep.id,
            )
            return

        try:
            with self.env.cr.savepoint():
                duplicate.unlink()
            _logger.info(
                "Merged duplicate variant %s into %s for template %s",
                duplicate.id, keep.id, self.display_name,
            )
        except Exception:
            _logger.warning(
                "Variant %s (template %s) still has other references (stock/accounting) "
                "after moving its sale/purchase order lines to %s - left in place, please "
                "review it manually.", duplicate.id, self.display_name, keep.id,
            )
