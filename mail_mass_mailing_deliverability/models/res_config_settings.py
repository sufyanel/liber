from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mail_mail_queue_batch_size = fields.Integer(
        string="Outgoing queue batch size",
        default=40,
        config_parameter="mail.mail.queue.batch.size",
    )
    mail_session_batch_size = fields.Integer(
        string="SMTP session batch size",
        default=50,
        config_parameter="mail.session.batch.size",
    )
    mail_compose_batch_size = fields.Integer(
        string="Mass mail generation batch size",
        default=40,
        config_parameter="mail.batch_size",
    )
    mail_mail_force_send_limit = fields.Integer(
        string="Direct send recipient limit",
        default=80,
        config_parameter="mail.mail.force.send.limit",
    )
