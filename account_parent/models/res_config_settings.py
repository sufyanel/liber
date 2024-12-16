# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2020 - Today O4ODOO (Omal Bastin)
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    parent_account_loaded = fields.Boolean("Load Parent accounts",
                                           help="If you have an parent account chart template already imported and want"
                                                " to load for this company ")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        if self.chart_template and self.parent_account_loaded:
            self.chart_template.update_generated_account(code_digits=self.chart_template.code_digits,
                                                            importing_parent=True)
