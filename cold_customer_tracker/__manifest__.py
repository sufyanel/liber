{
    'name': 'Cold Customer Tracker',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Track customers with no invoices in date range',
    'depends': ['contacts', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cold_customer_wizard_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}
