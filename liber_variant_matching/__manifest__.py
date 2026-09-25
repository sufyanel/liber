{
    'name': 'Liber Variant Matching',
    'version': '17.0.1.1.0',
    'summary': 'Orders and the website always resolve to the real stocked variant',
    'description': """
Odoo finds the variant for a chosen brand by comparing internal attribute-value
IDs exactly. Variants imported with extra "Never" values, outdated values or a
re-imported attribute therefore never match, and Odoo creates empty duplicates.

This module changes only the matching: when a variant with an internal
reference has the same brand / variant values (compared by name, ignoring
"Never" specs and outdated records), that variant is used. It applies to
backend quotations, the product configurator, website stock and price display,
and the website cart. No product data is changed.
""",
    'author': 'Axiom World',
    'category': 'Sales/Sales',
    'depends': ['product'],
    'license': 'LGPL-3',
    'installable': True,
}
