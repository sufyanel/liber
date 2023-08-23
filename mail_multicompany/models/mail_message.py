# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class MailMessage(models.Model):
    _inherit = "mail.message"

    company_id = fields.Many2one("res.company", "Company")
    branch_id = fields.Many2one("res.branch", "Branch")

    @api.model_create_multi
    def create(self, values_list):
        for vals in values_list:

            # Company
            if vals.get("model") and vals.get("res_id"):
                current_object = self.env[vals["model"]].browse(vals["res_id"])
                if hasattr(current_object, "company_id") and current_object.company_id:
                    vals["company_id"] = current_object.company_id.id
            if not vals.get("company_id"):
                vals["company_id"] = self.env.company.id

            # Branch
            if vals.get("model") and vals.get("res_id"):
                current_object = self.env[vals["model"]].browse(vals["res_id"])
                if hasattr(current_object, "branch_id") and current_object.branch_id:
                    vals["branch_id"] = current_object.branch_id.id
            if not vals.get("branch_id"):
                vals["branch_id"] = self.env.branch.id

            if not vals.get("mail_server_id"):
                vals["mail_server_id"] = (self.env["ir.mail_server"].search(
                    [("company_id", "=", vals.get("company_id", False)),
                     ("branch_id", "=", vals.get("branch_id", False))], order="sequence", limit=1, ).id)
                mail_server = self.env["ir.mail_server"].search([("company_id", "=", vals.get("company_id", False)),
                                                                 ("branch_id", "=", vals.get("branch_id", False))],
                                                                order="sequence", limit=1, )
                if mail_server:
                    vals["email_from"] = mail_server.smtp_user
                # else:
                #     current_object = self.env[vals["model"]].browse(vals["res_id"])
                #     raise ValidationError(_(
                #         "No Mail Server Found For Company '%s' and Branch '%s'.",
                #         current_object.company_id.name, current_object.branch_id.name,
                #     ))
        return super(MailMessage, self).create(vals)
