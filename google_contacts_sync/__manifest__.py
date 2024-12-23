{
    'name': "Google Contacts Sync",
    'version': '17.0',
    'summary': "Sync Google Contacts into Odoo",
    'description': "This module will help you sync all of your google contacts into odoo",
    'category': 'Tools',
    'author': 'AxiomWorld',
    'company': 'Axiom World Pvt. Ltd.',
    'maintainer': 'AxiomWorld',
    'depends': ['contacts'],
    'website': 'https://www.axiomworld.net',
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_ext.xml',
        'views/res_company_ext.xml',
        'views/google_labels.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'google_contacts_sync/static/src/js/owl_partner_list.js',
            'google_contacts_sync/static/src/js/owl_partner_kanban.js',
            'google_contacts_sync/static/src/xml/google_contacts_sync_button_tree.xml',
            'google_contacts_sync/static/src/xml/owl_partner_kanban.xml',

        ],
    },

    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
}
