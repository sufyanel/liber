# -*- coding: utf-8 -*-

{
    'name': 'Asset Number Customization',
    'description': """Asset Number Customization""",
    'version': '15.0.0.0.0',
    'author': 'Farooq Butt/Axiom World Team',
    'company': 'Axiom World Pvt. Ltd.',
    'maintainer': 'Axiom World Pvt. Ltd.',
    'website': 'https://axiomworld.net',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'stock',
        'sale_management',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_ext.xml',
        'views/customer_part_number.xml',
        'views/sale_order_line_ext.xml',

        'report/sale_report_templates_ext.xml',
        'report/delivery_slip_inventory.xml',
        'report/invoice_report.xml'
    ],
    'installable': True,
    'auto_install': False,
}
