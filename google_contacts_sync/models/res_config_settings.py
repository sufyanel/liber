from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_contacts_client_identifier = fields.Char('Google Client Id', config_parameter='google_contacts_client_id')
    google_contacts_client_secret = fields.Char('Google Client Secret', config_parameter='google_contacts_client_secret')
