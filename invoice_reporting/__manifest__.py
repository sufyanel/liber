{
    'name': 'Invoice Reporting',
    'version': '17.0.1.0.1',
    'category': 'Accounting',
    'summary': 'Invoice comparison reports',
    'depends': ['account', 'account_budget', 'analytic'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/invoice_comparison_wizard_view.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
}