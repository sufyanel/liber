# -*- coding: utf-8 -*-
"""17.0.1.1.0: the percentage changes from MARKUP to GROSS MARGIN (Dale, 7 Oct 2026).

Convert every stored percentage to the margin that gives the same price, so no price moves on upgrade:
markup m%  ->  margin m / (100 + m) * 100      (100% markup -> 50% margin; 15% -> 13.04%)
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE product_pricelist_item
           SET percentage_extra = percentage_extra * 100.0 / (100.0 + percentage_extra)
         WHERE percentage_extra IS NOT NULL AND percentage_extra > 0
    """)
    cr.execute("""
        UPDATE pricelist_tier
           SET percentage = percentage * 100.0 / (100.0 + percentage)
         WHERE percentage IS NOT NULL AND percentage > 0
    """)
