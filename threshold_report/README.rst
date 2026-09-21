=================
Threshold Report
=================

This module generates a Financial Security Threshold report: a cash-flow
analysis combining posted accounting data with a handful of manual inputs,
exported as an Excel workbook.

**Table of contents**

.. contents::
   :local:

Configuration
=============

* Go to *Accounting > Configuration > Accounting > Threshold Report
  Accounts* to map each report row (Salary, Depreciation, Change in
  Accounts Receivable, Change in Accounts Payable, Change in Inventory,
  Debt Retirement, Investor Return, Capital Investments, Savings, Taxes) to
  one or more accounts, each with a percentage weight, or to a single
  manual amount. A row with account lines is computed from those accounts;
  a row with no lines and no mapping at all falls back to the matching
  manual field on the report wizard (Capital Investments, Savings, Tax,
  Investor Return).

* Each account mapping row includes a *Use Period Change (Closing − Opening)*
  checkbox. When unchecked (the default for most rows), the report sums the
  account's posted balance during the printed period only. When checked, the
  report instead fetches the account's balance as of the period's opening date
  and as of its closing date, and reports the difference between them. For
  example, for a period of January 1 – March 31, it retrieves the balance as
  of December 31 (opening) and as of March 31 (closing), then reports the
  difference. The *Use Period Change* checkbox is available on all rows
  except "Change in Accounts Payable". On module upgrade, existing mappings
  for "Change in Accounts Receivable" and "Change in Inventory" are
  automatically switched on, since those rows already behaved this way before
  the checkbox was introduced.

* The *Change in Accounts Payable* row is always computed as the difference
  between the amount owed as of the period's opening date and the amount owed
  as of the period's closing date. It uses historical account state to
  reconstruct what was actually owed on each matched bill at those two points
  in time, rather than a snapshot of today's live residual amount. This ensures
  the report accurately reflects cash flow during the specified period, even if
  bills have since been paid or adjusted.

* Go to *Accounting > Configuration > Companies* and set *Related Company*
  and *Required Threshold Report* on any company that should appear in the
  Threshold Report wizard's company selector.

Usage
=====

* Go to *Accounting > Reporting > Threshold Report*.
* Pick the company, the period (year, quarter, or month), and any manual
  values that are not covered by an account mapping.
* Click *Download Excel Report* to generate the workbook.

Bug Tracker
===========

Bugs and feature requests are tracked internally. Please contact the
module's author with a detailed description and steps to reproduce.

Credits
=======

Authors
~~~~~~~

* Your Company
