# axiom_income_statement 17.0.6.1.0

| Requirement | Source | Status |
|---|---|---|
| Expense % column (each line as a share of sales) | Dale, 14 Aug 2026 | In place |
| Cross-company GL account mapping (e.g. Roger Brown accounts into RBC Industrial) | Dale, 14 Aug 2026 | In place: a mapped account of another company always counts and that company is combined in |
| One menu area for report, account mapping and budget allocation | Dale, 14 Aug 2026 | Done: Accounting > Reporting > Income Statement > Dashboard / Account Mapping / Budget Allocation / Dashboard Settings |
| Income Statement dashboard | Dale, 2 Oct 2026 | In place |
| No Excel download report | Dale, 23 Oct 2026 | The old "Income Statement" Excel wizard menu is removed (inactive) |
| Q1-Q4 and FY tabs; Custom shows the date range only when selected | 23 Oct 2026 (as Invoice Comparison) | Done |
| Automatic recalculation when a custom date changes (no Calculate button) | 23 Oct 2026 (as Invoice Comparison) | Done, about one second |
| Refresh by itself when opened and older than one hour; rebuild every dashboard on install / upgrade | as Invoice Comparison | Done |

Tested on Odoo 17: imported from the frontend, menus consolidated, Excel menu inactive, tabs and Custom range,
automatic recalculation in about 1 second, figures exact against posted invoices (FY revenue 4,500.00 = invoices),
dashboard rebuilt during the upgrade, no JavaScript or server errors.

Archived records: the statement adds up posted journal items by account, so entries of archived customers and of retired (deprecated) accounts are always included. Tested: FY revenue unchanged (4,500.00) with archived customers and the sales account deprecated.
