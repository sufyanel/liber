# Copyright 2020-22 Manish Kumar Bohra <manishkumarbohra@outlook.com>
# License LGPL-3 - See http://www.gnu.org/licenses/Lgpl-3.0.html

{
    'name': 'Bulk Confirm Quotations',
    'version': '17.0',
    'summary': 'This app allows you to confirm multiple sales order in bulk',
    'description': 'This app allows you to confirm multiple sales order in bulk',
    'category': 'Sales',
    'author': 'Manish Bohra || Axiom Team',
    'website': 'www.linkedin.com/in/manishkumarbohra',
    'maintainer': 'Manish Bohra',
    'support': 'manishkumarbohra@outlook.com',
    'sequence': '10',
    'license': 'LGPL-3',
    "data": [
        'views/bulk_sales.xml',
    ],
    'images': ['static/description/bulk.gif'],
    'depends': ['sale', 'sale_management'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
