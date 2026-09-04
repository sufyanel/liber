---------------------------------
Product Variant Combination Fix
---------------------------------

One-time data-fix utility. Install it, run its scheduled action once
against production, confirm everything is clean, then uninstall it - it
adds no fields and owns no other data, so nothing is left behind.

**Table of contents**

Background:
-----------

A product variant's defining combination must only contain values from
`always`/`dynamic` attributes. Some existing variants (first found on
`M10-025`) also carry values from `no_variant` ("Never") attributes in
their combination - most likely left over from when those attributes were
still `always`/`dynamic`. Because of that, Odoo can no longer match those
variants against a new sale/purchase order for the same real product, and
creates a brand new duplicate variant instead of reusing the existing one.

Installation:
-------------

Depends on `product`, `sale` and `purchase`.

Usage:
------

Go to Settings > Technical > Scheduled Actions > "Fix Polluted Variant
Combinations" and click "Run Manually". It is intentionally not scheduled
to run on its own.

One run scans the whole database for every product template that actually
has this corruption - no list to maintain, and nothing to run again on a
schedule. For each one found, it keeps the oldest variant per real
(no_variant-values-excluded) combination, whether or not a duplicate has
already been created for it: moves any sale/purchase order lines pointing
at a newer duplicate onto the kept variant, deletes that duplicate, and
strips the stale `no_variant` links so future orders match it correctly.
If a duplicate still has other references (stock moves, invoice lines) or
its order lines can't be moved (locked/invoiced/delivered order), it is
left in place with a warning in the log for manual review; that does not
stop the run from fixing every other affected product.

Once the log shows nothing left to review, this module can be
uninstalled.

Authors:
--------
* Axiom World Team

Developer:
----------
* Axiom World Pvt. Ltd. <https://axiomworld.net>
