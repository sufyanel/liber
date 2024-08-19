# -*- coding: utf-8 -*-

{
    'name': 'Liber customization',
    'description': """Liber Customization""",
    'version': '15.0.0.0.0',
    'author': 'Adnan khan/Axiom World Team',
    'company': 'Axiom World Pvt. Ltd.',
    'maintainer': 'Axiom World Pvt. Ltd.',
    'website': 'https://axiomworld.net',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'stock',
        'sale_management',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'report/sale_report_templates_ext.xml',
        'report/delivery_slip_inventory.xml',
        'report/invoice_report.xml',
        'report/product_label_layout_report_ext.xml',
        'report/report_delivery_slip_ext.xml'

    ],
    'installable': True,
    'auto_install': False,
}
