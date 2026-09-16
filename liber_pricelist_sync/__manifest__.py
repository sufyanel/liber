# -*- coding: utf-8 -*-
{
    'name': 'Liber Pricelist Sync & Tier Customization',
    'summary': 'Custom pricelist vendor cost sync, percentage calculations, and partner/pricelist tier management',
    'description': """
        Liber Pricelist Sync & Tier Customization Module:
        - Relational Tier model (pricelist.tier) for contacts and pricelists.
        - Vendor cost and percentage extra fields with dynamic forward and reverse calculations on pricelist items.
        - Sync vendor prices button on pricelists fetching latest prices from confirmed purchase orders with posted vendor bills.
        - Syncs vendor prices only for existing products in the pricelist without adding new products.
    """,
    'version': '17.0.1.0.0',
    'category': 'Sales/Pricelist',
    'author': 'Liber / Axiom World',
    'website': 'https://axiomworld.net',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'sale_management',
        'purchase',
        'account',
        'contacts',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/pricelist_tier_views.xml',
        'views/res_partner_views.xml',
        'views/product_pricelist_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
