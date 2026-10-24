# axiom_invoice_comparison 17.0.5.5.0 - Dale, 23 Oct 2026 meeting

| Item | Change |
|---|---|
| El Paso Water plants and the Adler duplicate showed as separate customers | New "Report Under (dashboards)" field on every contact (companies, people, archived contacts). Set it to the customer the sales belong to; the dashboards consolidate them there. No merging, invoices unchanged |
| Archived customers | Never listed on the dashboard (17.0.5.4.0). An archived duplicate that has Report Under set to an active customer still adds its sales to that customer |
| Excel download confused users | The "Invoice Comparison (Excel)" menu is removed (inactive) - the dashboard is the one to use |
| "New" customer badge | Tooltip explains the rule: no sales in the same period of the previous year (use Year to Date to see new customers for the year) |
| Period selector | Q1-Q4 and full-year buttons kept; the From / To date range appears only when Custom is selected |
| Auto refresh | Choosing Custom calculates straight away, and changing a date recalculates by itself (no Calculate or Refresh click). Quick successive changes are combined into one calculation. Quarters and full year switch instantly |
| Tested | Dashboard opened and calculated in about 2 seconds; a date change recalculated in about 1 second; archived customer excluded; plant consolidated under its customer |
| Archived customers still showing (live) | Cause: the dashboard shows a saved snapshot, rebuilt only nightly or on Refresh, so rows calculated before the upgrade or before a customer was archived stayed. Now every dashboard is rebuilt on install / upgrade, and a dashboard older than one hour refreshes itself when opened |
| Contacts of an archived company | An active contact (plant, AP contact) of an archived company is excluded too, unless Report Under points it to an active customer |
| Tested | Stale snapshot with an archived customer and an archived company's plant: both gone right after the upgrade; a 2-hour-old snapshot refreshed on opening and dropped a customer archived after it |
| 17.0.5.4.1 | A background refresh (stale snapshot) keeps the tab the user is on instead of switching to Custom |
| 17.0.5.5.0 | One menu area, as for the Income Statement: Accounting > Reporting > Invoice Comparison > Dashboard / Dashboard Settings |
