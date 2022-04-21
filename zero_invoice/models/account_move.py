# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.


from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_bank_accounts(self):
        data1 = []
        data2 = []

        for vals in self:
            banks = vals.company_id.partner_id.bank_ids
            total = len(vals.company_id.partner_id.bank_ids)
            len1 = total // 2
            len2 = total - len1
            for i in range(len2):
                data1.append(banks[i])

            for j in range(len2, total):
                data2.append(banks[j])

        return data1, data2
