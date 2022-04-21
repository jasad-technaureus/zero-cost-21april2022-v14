# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import fields, models, api
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
    _inherit = 'account.move'

    currency_company = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)

    # @api.depends('name', 'state')
    # def name_get(self):
    #     result = []
    #     for move in self:
    #         if self._context.get('name_groupby'):
    #             name = '%s, %s' % (format_date(self.env, move.date), move._get_move_display_name())
    #             print('initial NAMMMMMMMMME',name)
    #             if move.ref:
    #                 name += '     (%s)' % move.ref
    #             if move.partner_id.name:
    #                 name += ' - %s' % move.partner_id.name
    #         else:
    #             name = move._get_move_display_name(show_ref=True)
    #         print('FINALLLLL',name)
    #         result.append((move.id, name))
    #     return result

    @api.depends('amount_untaxed')
    def _get_untaxed_amt(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.untaxed_amount_in_currency = rec.amount_untaxed if rec.amount_untaxed > 0 else -1 * rec.amount_untaxed
            if rec.move_type in ['out_refund', 'in_refund']:
                rec.untaxed_amount_in_currency = -rec.amount_untaxed if rec.amount_untaxed > 0 else rec.amount_untaxed

    @api.depends('amount_tax')
    def _get_tax_amt(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.tax_amount_in_currency = rec.amount_tax if rec.amount_tax > 0 else -1 * rec.amount_tax
            if rec.move_type in ['out_refund', 'in_refund']:
                rec.tax_amount_in_currency = -rec.amount_tax if rec.amount_tax > 0 else rec.amount_tax

    @api.depends('amount_untaxed_signed')
    def _get_amount_untaxed_signed(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.real_amount_untaxed_signed = rec.amount_untaxed_signed if rec.amount_untaxed_signed > 0 else -1 * rec.amount_untaxed_signed
            if rec.move_type in ['out_refund', 'in_refund']:
                rec.real_amount_untaxed_signed = -rec.amount_untaxed_signed if rec.amount_untaxed_signed > 0 else rec.amount_untaxed_signed

    @api.depends('amount_tax_signed')
    def _get_amount_tax_signed(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.real_amount_tax_signed = rec.amount_tax_signed if rec.amount_tax_signed > 0 else -1 * rec.amount_tax_signed
            if rec.move_type in ['out_refund', 'in_refund']:
                rec.real_amount_tax_signed = -rec.amount_tax_signed if rec.amount_tax_signed > 0 else rec.amount_tax_signed

    @api.depends('amount_total_signed')
    def _get_amount_total_signed(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.real_amount_total_signed = rec.amount_total_signed if rec.amount_total_signed > 0 else -1 * rec.amount_total_signed
            if rec.move_type in ['out_refund', 'in_refund']:
                rec.real_amount_total_signed = -rec.amount_total_signed if rec.amount_total_signed > 0 else rec.amount_total_signed

    @api.depends('amount_total')
    def _get_currency_total(self):
        for rec in self:

            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.total_in_currency = rec.amount_total if rec.amount_total > 0 else -1 * rec.amount_total
            if rec.move_type in ['out_refund', 'in_refund']:
                rec.total_in_currency = -rec.amount_total if rec.amount_total > 0 else rec.amount_total

    @api.depends('amount_residual')
    def _get_due_amount(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.amount_due_in_currency = rec.amount_residual if rec.amount_residual > 0 else -1 * rec.amount_residual
            if rec.move_type in ['out_refund', 'in_refund']:
                rec.amount_due_in_currency = -rec.amount_residual if rec.amount_residual > 0 else rec.amount_residual

    untaxed_amount_in_currency = fields.Monetary('Tax Excluded in Currency', compute='_get_untaxed_amt', store=True)
    tax_amount_in_currency = fields.Monetary('Tax in Currency', compute='_get_tax_amt', store=True)
    total_in_currency = fields.Monetary('Total in Currency', compute='_get_currency_total', store=True)
    amount_due_in_currency = fields.Monetary('Amount Due in Currency', compute='_get_due_amount', store=True)
    real_amount_untaxed_signed = fields.Monetary('Tax Excluded', compute='_get_amount_untaxed_signed',
                                                 )
    real_amount_tax_signed = fields.Monetary('Tax', compute='_get_amount_tax_signed')
    real_amount_total_signed = fields.Monetary('Total', compute='_get_amount_total_signed')
    real_amount_residual_signed = fields.Monetary('Amount Due', compute='_get_real_amount_residual_signed')

    def _get_real_amount_residual_signed(self):
        for rec in self:
            if rec.move_type in ['out_invoice', 'in_invoice']:
                rec.real_amount_residual_signed = abs(rec.amount_residual_signed)
            elif rec.move_type in ['out_refund', 'in_refund']:
                amount = rec.amount_residual_signed
                if amount > 0:
                    amount = amount * -1
                rec.real_amount_residual_signed = amount


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _get_total(self):
        for rec in self:
            if rec.currency_id != rec.env.company.currency_id:
                # amount = rec.currency_id.compute(rec.price_total, self.env.company.currency_id)
                amount = rec.move_id.main_curr_rate * rec.real_total
                if rec.type in ['out_refund', 'in_refund']:
                    amount = -1 * amount
                rec.total_in_main_currency = amount
            else:
                if rec.type in ['out_refund', 'in_refund']:
                    rec.total_in_main_currency = -1 * rec.move_id.main_curr_rate * rec.real_total
                else:
                    rec.total_in_main_currency = rec.move_id.main_curr_rate * rec.real_total

    def _get_subtotal(self):
        for rec in self:
            if rec.currency_id != rec.env.company.currency_id:
                # amount = rec.currency_id.compute(rec.price_subtotal, self.env.company.currency_id)
                amount = rec.move_id.main_curr_rate * rec.real_subtotal
                if rec.type in ['out_refund', 'in_refund']:
                    amount = -1 * amount
                rec.subtotal_in_main_currency = amount
            else:
                if rec.type in ['out_refund', 'in_refund']:
                    rec.subtotal_in_main_currency = rec.move_id.main_curr_rate * rec.real_subtotal * -1
                else:
                    rec.subtotal_in_main_currency = rec.move_id.main_curr_rate * rec.real_subtotal

    @api.depends('price_total')
    def _get_real_total(self):
        for rec in self:
            if rec.type in ['out_invoice', 'in_invoice']:
                rec.real_total = rec.price_total if rec.price_total > 0 else -1 * rec.price_total
            if rec.type in ['out_refund', 'in_refund']:
                rec.real_total = -rec.price_total if rec.price_total > 0 else rec.price_total

    @api.depends('real_total', 'real_subtotal')
    def _get_real_tax(self):
        for rec in self:
            rec.real_tax = rec.real_total - rec.real_subtotal

    @api.depends('price_subtotal')
    def _get_real_subtotal(self):
        for rec in self:

            if rec.type in ['out_invoice', 'in_invoice']:
                rec.real_subtotal = rec.price_subtotal if rec.price_subtotal > 0 else -1 * rec.price_subtotal
            if rec.type in ['out_refund', 'in_refund']:
                rec.real_subtotal = - rec.price_subtotal if rec.price_subtotal > 0 else rec.price_subtotal

    @api.depends('quantity')
    def _get_qty(self):
        for rec in self:
            if rec.type in ['out_invoice', 'in_invoice']:
                rec.quantity_by_sign = rec.quantity if rec.quantity > 0 else -1 * rec.quantity
            if rec.type in ['out_refund', 'in_refund']:
                rec.quantity_by_sign = -rec.quantity if rec.quantity > 0 else rec.quantity

    product_code = fields.Char('Product Code', related='product_id.default_code')
    type = fields.Selection(related='move_id.move_type', store=True)
    subtotal_in_main_currency = fields.Monetary('Subtotal in Main Currency', compute='_get_subtotal')
    total_in_main_currency = fields.Monetary('Total in Main Currency', compute='_get_total')
    quantity_by_sign = fields.Float('Real Quantity', compute='_get_qty', store=True)
    real_subtotal = fields.Monetary('Real Subtotal', compute='_get_real_subtotal', store=True)
    real_tax = fields.Monetary('Real Tax', compute='_get_real_tax', store=True)
    real_total = fields.Monetary('Real Total', compute='_get_real_total', store=True)
    price_unit = fields.Float(string='Unit Price', digits='Product Price', group_operator=False)
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0, group_operator=False)
    # test = fields.Float(string='Discount (%)', digits='Discount',compute='_get_total',)
