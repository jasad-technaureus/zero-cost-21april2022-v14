# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields, api, exceptions


class AccountMove(models.Model):
    _inherit = 'account.move'

    not_in_book = fields.Boolean(string="Don't show in Book", default=False)
    customs = fields.Boolean(string='Customs', default=False)
    vendor_bill = fields.Many2one('account.move', string="Related Vendor Bill")
    rel_vendor = fields.Many2one('res.partner', string='Related Vendor')
    ref_2 = fields.Char(string='Invoice Serial Number', default="", copy=False)
    is_partial = fields.Boolean(string="Is a partial Move", default=False)

    @api.onchange('vendor_bill')
    def onchange_vendor_bill(self):
        if self.vendor_bill:
            if self.vendor_bill.partner_id:
                self.rel_vendor = self.vendor_bill.partner_id.id

    @api.onchange('ref_2')
    def search_invoice_serial(self):
        if self.ref_2:
            invoice_serial_no = self.env['account.move'].search([('ref_2', '=', self.ref_2)])
            if invoice_serial_no:
                raise exceptions.ValidationError("Invoice Serial Number Must be unique")

    # def action_post(self):
    #     for val in self:
    #         if val.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']:
    #             if not val.ref_2 or not val.ref:
    #                 raise exceptions.ValidationError("Please Input Invoice Number and Invoice Serial Number")
    #             else:
    #                 return super(AccountMove, val).action_post()
    #         else:
    #             return super(AccountMove, val).action_post()

    @api.model_create_multi
    def create(self, vals_list):
        if 'flag' in self._context:
            for value in vals_list:
                value['ref_2'] = False
        return super(AccountMove, self).create(vals_list)


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'
    manage_sale_purchase_book = fields.Boolean("Manage In Excel Report", default=False)

    def _prepare_default_reversal(self, move):
        # if self.manage_sale_purchase_book:
        res = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        if self.refund_method == 'refund':
            res['is_partial'] = True
            res['ref'] = False
            res['ref_2'] = False
        if self.refund_method == 'cancel':
            res['ref'] = False
            res['ref_2'] = False
        if self.refund_method == 'modify':
            res['ref'] = False
            res['ref_2'] = False


        return res

    def reverse_moves(self):
        if self.refund_method == 'modify':
            self.env.context = dict(self.env.context)
            self.env.context.update({
                'flag': '1',
            })

        return super(AccountMoveReversal, self).reverse_moves()
