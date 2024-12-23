from odoo import fields, models, api
import subprocess
from pathlib import Path
import webbrowser


class ResCompanyExt(models.Model):
    _inherit = 'res.company'

    google_credentials = fields.Text()
    google_token = fields.Text()

