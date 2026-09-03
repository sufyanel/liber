# -*- coding: utf-8 -*-

{
    'name': 'Product Variant Combination Fix',
    'summary': 'One-time data fix for products whose variants have a polluted combination',
    'version': '17.0.1.0.0',
    'author': 'Axiom World Team',
    'company': 'Axiom World Pvt. Ltd.',
    'maintainer': 'Axiom World Pvt. Ltd.',
    'website': 'https://axiomworld.net',
    'license': 'AGPL-3',
    'depends': [
        'product',
        'sale',
        'purchase',
    ],
    'data': [
        'data/ir_cron_fix_variant_combination.xml',
    ],
    'installable': True,
    'auto_install': False,
    # One-time data-fix utility: install it, run the scheduled action once,
    # then uninstall it. It adds no fields and owns no other data, so
    # uninstalling leaves nothing behind.
}
