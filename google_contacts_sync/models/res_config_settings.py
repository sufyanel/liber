from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_contacts_credentials = fields.Char(
        string='Google Contacts Credentials',
        config_parameter='google_contacts_credentials'
    )
