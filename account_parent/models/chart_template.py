# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 - 2020 Steigend IT Solutions (Omal Bastin)
#    Copyright (C) 2020 - Today O4ODOO (Omal Bastin)
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

from odoo import api, models


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"
    
    def generate_account(self, tax_template_ref, acc_template_ref, code_digits, company):
        account_dict = super(AccountChartTemplate, self).generate_account(
            tax_template_ref, acc_template_ref, code_digits, company
        )
        self._update_parent_accounts(company)
        return account_dict

    def _update_parent_accounts(self, company):
        account_obj = self.env['account.account'].with_context(show_parent_account=True)
        code_account_dict = {}

        for account in account_obj.search([('company_id', '=', company.id)], order='code'):
            if account.parent_id:
                continue
            prefix = account.code[:2]
            parent_account = account_obj.search(
                [('code', '=', prefix), ('company_id', '=', company.id), ('account_type', '=', 'view')], limit=1
            )
            if parent_account:
                account.parent_id = parent_account.id
                code_account_dict[account.code] = parent_account

        for code_prefix in ['bank_account_code_prefix', 'cash_account_code_prefix', 'transfer_account_code_prefix']:
            code_prefix_value = getattr(company, code_prefix, False)
            if code_prefix_value:
                parent_account = code_account_dict.get(code_prefix_value) or account_obj.search(
                    [('code', '=', code_prefix_value), ('account_type', '=', 'view'), ('company_id', '=', company.id)], limit=1
                )
                if parent_account:
                    account_obj.search([
                        ('code', 'like', f"{code_prefix_value}%"),
                        ('id', '!=', parent_account.id),
                        ('company_id', '=', company.id)
                    ]).write({'parent_id': parent_account.id})
    