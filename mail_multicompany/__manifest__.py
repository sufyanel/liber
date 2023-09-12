# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Email Gateway Multi company",
    "version": "15.0.0.1.0",
    "category": "Extra Tools",
    "author": "Odoo Community Association (OCA), " "Comunitea",
    "website": "https://github.com/OCA/multi-company",
    "license": "AGPL-3",
    "depends": ["mail", "crm", "base", "web"],
    "data": ["security/mail_security.xml",
             "views/ir_mail_server_view.xml",
             "views/mail_alias.xml"],
    'assets': {
        'web.assets_backend': [
            'mail_multicompany/static/src/js/*.js',
        ],
    },
    "installable": True,
}
