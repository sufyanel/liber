{
    'name': 'Threshold Report',
    'version': '17.0.1.0.1',
    'category': 'Accounting',
    'summary': 'Financial Security Threshold Report',
    'description': """
        Generate comprehensive threshold reports with cash flow analysis,
        capital investments, and financial security calculations.
    """,
    'author': 'Your Company',
    'depends': ['account', 'base', 'purchase', 'sale', 'sale_purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/threshold_report_wizard_view.xml',
        'views/menu_views.xml',
        'views/res_cpmpany_views_ext.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}