# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveLineDiscountAllocationFix(models.Model):
    """
    Fixes a self-triggered infinite recursion in core Odoo's Discount
    Allocation feature when posting/writing invoices:

        RecursionError: maximum recursion depth exceeded while calling
        a Python object

    Root cause (odoo/addons/account/models/account_move_line.py,
    `_compute_discount_allocation_needed`):

        for line in self.move_id.line_ids:
            line.discount_allocation_dirty = True
            ...

    That loop assigns to EVERY line of the move, not just the
    recordset (`self`) Odoo actually asked this compute method to
    fill in. Odoo only marks the records it explicitly hands to a
    compute method as "protected" (safe to update in cache only,
    see `Field.compute_value()` -> `env.protecting(...)`). Any line
    outside that subset falls through to the "full business logic"
    branch of `Field.__set__`, which turns the assignment into a real
    `account.move.line.write()`.

    That `write()` calls `_field_will_change()` to decide whether the
    write is a no-op, which reads the field back (`record[field_name]
    != vals[field_name]`). Reading an uncached compute field triggers
    a *new* call to `_compute_discount_allocation_needed`, which loops
    over the same sibling lines again, writes to them again, and so
    on -- recursing until Python's stack limit is hit.

    Fix: extend Odoo's own "protecting" mechanism to cover every line
    this compute method touches (`self.move_id.line_ids`), exactly the
    way `Field.compute_value()` already protects the subset it was
    asked to compute. Every assignment inside the loop then goes
    through the safe, cache-only path instead of a real `write()` --
    no business logic, no recursion, and no change whatsoever to the
    computed result.
    """
    _inherit = 'account.move.line'

    def _compute_discount_allocation_needed(self):
        dirty_field = self._fields['discount_allocation_dirty']
        # Fields sharing this compute method (discount_allocation_needed and
        # discount_allocation_dirty) -- mirrors what Field.compute_value()
        # itself protects for the records it was asked to compute.
        shared_fields = self.pool.field_computed.get(dirty_field, [dirty_field])
        with self.env.protecting(shared_fields, self.move_id.line_ids):
            super(AccountMoveLineDiscountAllocationFix, self)._compute_discount_allocation_needed()