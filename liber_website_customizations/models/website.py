from odoo import api, models

from ..hooks import _enable_shop_attribute_views, _tune_attribute_display


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _liber_setup_shop_attribute_filters(self):
        """Enable hybrid shop filters; runs on module install and upgrade."""
        _enable_shop_attribute_views(self.env)
        _tune_attribute_display(self.env)
