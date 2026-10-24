from odoo import fields, models

from .blog_auto_translate_mixin import LIBRE_URL_PARAM, PROVIDER_PARAM


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    blog_translate_provider = fields.Selection(
        [
            ("google", "Google (free, no account)"),
            ("libre", "LibreTranslate (self-hosted)"),
        ],
        default="google",
        config_parameter=PROVIDER_PARAM,
        help="Both are free. Google needs nothing at all but is a public "
             "endpoint that answers when it feels like it; a LibreTranslate "
             "instance of your own has no such limit.",
    )
    blog_translate_libre_url = fields.Char(
        string="LibreTranslate URL",
        config_parameter=LIBRE_URL_PARAM,
        help="Address of your LibreTranslate instance, for example "
             "http://localhost:5000/translate",
    )
