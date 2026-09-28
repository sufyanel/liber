# -*- coding: utf-8 -*-
from odoo import api, models

from ..hooks import _configure_rbc_industrial


class Website(models.Model):
    _inherit = "website"

    @api.model
    def _rbc_theme_setup(self):
        _configure_rbc_industrial(self.env)
