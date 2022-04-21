# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import fields, models, api
from datetime import date


class AccountReportGeneralLedger(models.TransientModel):
    _inherit = "account.report.general.ledger"

    account_ids = fields.Many2many('account.account', string='Accounts')

    def _print_report(self, data):
        res = super(AccountReportGeneralLedger, self)._print_report(data)
        data['form'].update(self.read(['account_ids'])[0])
        return res


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    date_from = fields.Date(string='Start Date', default=date.today())
    date_to = fields.Date(string='End Date', default=date.today())
