# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('amount_untaxed', 'amount_tax', 'discount_type', 'discount_rate', 'order_line.price_total',
                 )
    def _amount_all(self):

        res = super(PurchaseOrder, self)._amount_all()
        for order in self:
            order.amount_grand = order.amount_total
            if order.discount_type == 'percent':

                if order.discount_rate > 100:
                    raise UserError(_(
                        "Discount percentage cannot be  more than 100"))

                order.amount_discount = round((order.amount_grand * order.discount_rate / 100), 2)
            elif order.discount_type == 'amount':
                if order.discount_rate > order.amount_grand:
                    raise UserError(_(
                        "Discount amount cannot be  more than total value"))
                order.amount_discount = order.discount_rate
            if order.amount_grand >= order.amount_discount:
                order.amount_total = order.amount_grand - order.amount_discount
        return res

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], 'Discount Type',
                                     readonly=True, default='percent', states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate', readonly=True, states={'draft': [('readonly', False)]})
    discount_narration = fields.Char('Discount Narration', readonly=True, states={'draft': [('readonly', False)]})
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                  readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount', digits='Account',
                                   store=True, readonly=True, compute='_amount_all')
    amount_grand = fields.Float(string='Total', digits='Account',
                                store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Float(string='Net Total', digits='Account',
                                store=True, readonly=True, compute='_amount_all')

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        sale_purchase_global_discount = self.env['ir.config_parameter'].sudo().get_param(
            'tis_sales_purchase_global_discount.sale_purchase_global_discount')
        if sale_purchase_global_discount == 'True':
            res['discount_type'] = self.discount_type
            res['discount_rate'] = self.discount_rate
            res['discount_narration'] = self.discount_narration
            res['analytic_id'] = self.analytic_id
            res['amount_discount'] = self.amount_discount
        # res['amount_grand'] = self.amount_grand
        return res
