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
