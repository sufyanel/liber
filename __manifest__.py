# -*- coding: utf-8 -*-
{
    'name': 'Liber Pricelist Sync & Tier Customization',
    'summary': 'Website price from vendor cost with gross margin: vendor price list, then vendor bill, then average cost',
    'description': """
        Liber Pricelist Sync & Tier Customization Module:
        - Relational Tier model (pricelist.tier) for contacts and pricelists.
        - Vendor cost and gross margin fields with forward and reverse calculations on pricelist items
          (price = cost / (1 - gross margin)).
        - Sync Vendor Prices: cost is taken from (1) the top line of the product's vendor price list,
          (2) the latest posted vendor bill, (3) the average cost - in that order (Dale, 7 Oct 2026).
        - Creates pricelist items for products that do not have one yet, so every product can be listed.
        - Cost Rule per pricelist: vendor price list first (default) or the higher of vendor price list and last bill.
        - The sync result lists the products skipped for having no cost anywhere.
    """,
    'version': '17.0.1.2.0',
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
