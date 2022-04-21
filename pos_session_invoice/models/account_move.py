# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields, api


# class AccountMove(models.Model):
#     _inherit = 'account.move'
#
#     def _stock_account_get_last_step_stock_moves(self):
#         res = super(AccountMove, self)._stock_account_get_last_step_stock_moves()
#         print("RESssssssssss", res)
#         if "pospicking_new" in self.env.context:
#             res += self.env.context["pospicking_new"].move_lines.filtered(
#                 lambda x: x.state == 'done' and x.location_dest_id.usage == 'customer')
#             print("resssssss2", res)
#         return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('from_pos'):
            if len(vals_list) > 0:
                for data in vals_list:
                    if data.get('partner_id'):
                        data['partner_id'] = self.env.context.get('config_partner')

        res = super(AccountMoveLine, self).create(vals_list)
        return res
