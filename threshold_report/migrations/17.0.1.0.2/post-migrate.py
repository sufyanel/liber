def migrate(cr, version):
    """The new use_balance_change field defaults to False. Change in
    Accounts Receivable and Change in Inventory already computed a
    closing-minus-opening balance before this field existed, so switch
    existing mapping rows for those two keys on to keep that behaviour -
    otherwise upgrading this module would silently change already-printed
    report totals."""
    cr.execute(
        """
        UPDATE threshold_report_account_mapping
           SET use_balance_change = TRUE
         WHERE row_key IN ('change_ar', 'change_inventory')
        """
    )
