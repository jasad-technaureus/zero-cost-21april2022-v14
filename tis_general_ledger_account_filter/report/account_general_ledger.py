# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

import time
import logging
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportGeneralLedger(models.AbstractModel):
    _inherit = 'report.accounting_pdf_reports.report_general_ledger'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        models = self.env.context.get('active_model')
        docs = self.env[models].browse(self.env.context.get('active_ids', []))

        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]
        if data['form']['account_ids']:
            accounts = self.env['account.account'].search([('id', 'in', data['form']['account_ids'])])
        else:
            accounts = docs if models == 'account.account' else self.env['account.account'].search([])
        accounts_res = self.with_context(data['form'].get('used_context', {}))._get_account_move_entry(accounts,
                                                                                                       init_balance,
                                                                                                       sortby,
                                                                                                       display_account)
        return {
            'doc_ids': docids,
            'doc_model': models,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
        }
