from odoo import models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @staticmethod
    def _liber_variant_key(ptavs):
        """Brand / variant values by name, ignoring 'Never' specs."""
        return frozenset(
            ((p.attribute_id.name or '').strip().lower(), (p.name or '').strip().lower())
            for p in ptavs
            if p.attribute_id.create_variant != 'no_variant'
        )

    def _liber_real_variant(self, filtered_combination):
        """The existing variant that is this part, by brand / variant values (by name).

        1. the one variant with an internal reference (the real stocked part);
        2. otherwise an existing variant with the same values (a copy made
           earlier), so that no NEW copy is created: active first, then the one
           with stock, then the oldest.
        Returns an empty recordset when nothing matches or the choice is not safe.
        """
        self.ensure_one()
        Product = self.env['product.product']
        key = self._liber_variant_key(filtered_combination)
        if not key:
            return Product
        same = Product.with_context(active_test=False).search([('product_tmpl_id', '=', self.id)]).filtered(
            lambda v: self._liber_variant_key(v.product_template_attribute_value_ids) == key)
        if not same:
            return Product
        with_ref = same.filtered(lambda v: (v.default_code or '').strip())
        active_ref = with_ref.filtered('active')
        if len(active_ref) == 1:
            return active_ref
        if len(active_ref) > 1:
            return Product  # two real parts for the same brand: do not guess
        if len(with_ref) == 1:
            return with_ref  # real part archived by mistake
        if with_ref:
            return Product
        active = same.filtered('active')
        pool = active or same
        return pool.sorted('id')[:1]  # the oldest copy, always the same one

    def _get_variant_id_for_combination(self, filtered_combination):
        variant_id = super()._get_variant_id_for_combination(filtered_combination)
        variant = self.env['product.product'].browse(variant_id)
        if variant and variant.active and (variant.default_code or '').strip():
            return variant_id  # standard match is already the real part
        real = self._liber_real_variant(filtered_combination)
        if not real:
            return variant_id
        if variant and variant.active and not (real.default_code or '').strip():
            return variant_id  # standard match is an active copy already: keep Odoo's choice
        return real.id

    def _create_product_variant(self, combination, log_warning=False):
        variant = super()._create_product_variant(combination, log_warning=log_warning)
        if variant and not variant.active and (variant.default_code or '').strip():
            # a real part archived by mistake: bring it back instead of selling an archived product
            variant.sudo().write({'active': True})
        return variant
