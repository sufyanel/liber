from odoo import api, fields, models, _

class SaleOrderExt(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrderExt, self).action_confirm()
        for move in self.order_line.move_ids:
            move.write({
                'description_picking' : move.sale_line_id.name,
            })
        return res
