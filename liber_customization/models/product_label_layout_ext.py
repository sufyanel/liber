from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductLabelLayoutExt(models.TransientModel):
    _inherit = 'product.label.layout'

    # adding new label field
    print_format = fields.Selection(selection_add=[('demo_label', 'Demo V.8 2010'), ('2x7xprice',) ],
                                    ondelete={'demo_label': 'cascade'}, default='demo_label',)







    def _prepare_report_data(self):
        # xml_id = False
        # Your custom logic first
        if 'demo_label' in self.print_format:
            xml_id = 'liber_customization.action_print_label_pdf'
            # Build data to pass to the report
            data = {}
        else:
            # Call superclass method to get xml_id and data
            xml_id, data = super(ProductLabelLayoutExt, self)._prepare_report_data()
        return xml_id, data

    def process(self):
        self.ensure_one()
        if 'demo_label' in self.print_format:
            xml_id, data = self._prepare_report_data()  # Call the custom method to prepare report data
            if not xml_id:
                raise UserError(_('Unable to find report template for %s format', self.print_format))
            # Get the report action reference and execute with prepared data
            report_action = self.env.ref(xml_id).report_action(None, data=data)
            # Set additional attribute to close the report on download
            report_action.update({'close_on_report_download': True})
        else:
            report_action = super(ProductLabelLayoutExt, self).process()  # Call the superclass method 'process'
        return report_action  # Return the report action object
