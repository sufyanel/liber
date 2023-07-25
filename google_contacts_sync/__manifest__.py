{
    'name': "Google Contacts Sync",
    'version': '15.0.0.0.0',
    'summary': "Sync Google Contacts into Odoo",
    'description': "This module will help you sync all of your google contacts into odoo",
    'category': 'Tools',
    'author': 'AxiomWorld',
    'company': 'Axiom World Pvt. Ltd.',
    'maintainer': 'AxiomWorld',
    'depends': ['contacts'],
    'website': 'https://www.axiomworld.net',
    'data': [
        'views/res_partner_ext.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'google_contacts_sync/static/src/js/*.js',
        ],
        'web.assets_qweb': [
            'google_contacts_sync/static/src/xml/*.xml',
        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
