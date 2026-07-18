from odoo import api, models

from ..hooks import _set_shop_filter_views, _tune_attribute_display


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _liber_setup_shop_attribute_filters(self):
        """Enable drawer-only shop filters; runs on module install and upgrade."""
        _set_shop_filter_views(self.env)
        _tune_attribute_display(self.env)
