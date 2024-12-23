from odoo import fields, models, api
from random import randint


class GoogleLabels(models.Model):
    _name = 'google.labels'
    _description = 'Google Labels'

    name = fields.Char()
    color_picker = fields.Integer()

    # method for random number so we can have different color for each record
    @api.model
    def create(self, vals):
        vals['color_picker'] = randint(1, 11)
        return super(GoogleLabels, self).create(vals)
