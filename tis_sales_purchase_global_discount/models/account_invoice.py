# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _, exceptions

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
from ast import literal_eval


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id',
        'discount_type',
        'discount_rate'
    )
    def _compute_amount(self):
        for rec in self:
            res = super(AccountMove, self)._compute_amount()
            sale_purchase_global_discount = self.env['ir.config_parameter'].sudo().get_param(
                'tis_sales_purchase_global_discount.sale_purchase_global_discount')

            if sale_purchase_global_discount == 'True':
                rec.amount_grand = rec.amount_untaxed + rec.amount_tax
                if (rec.discount_type == 'percent'):
                    if rec.discount_rate > 100:
                        raise exceptions.ValidationError("Discount percentage cannot be more than 100")
                    rec.amount_discount = round((rec.amount_grand * rec.discount_rate / 100), 2)
                elif (rec.discount_type == 'amount'):
                    if rec.discount_rate > rec.amount_grand:
                        raise exceptions.ValidationError(
                            "Discount amount cannot be  more than the value of the Invoice")
                    rec.amount_discount = rec.discount_rate
                if (rec.amount_grand >= rec.amount_discount):
                    rec.amount_total = rec.amount_grand - rec.amount_discount
                amount_untaxed_signed = rec.amount_untaxed
                if rec.currency_id and rec.company_id and rec.currency_id != rec.company_id.currency_id:
                    currency_id = rec.currency_id.with_context(date=rec.invoice_date)
                    amount_untaxed_signed = currency_id.compute(rec.amount_untaxed, rec.company_id.currency_id)
                sign = rec.move_type in ['in_refund', 'out_refund'] and -1 or 1
                rec.amount_total_signed = rec.amount_total * sign
                rec.amount_untaxed_signed = amount_untaxed_signed * sign
            else:
                rec.amount_discount = 0.0

            return res

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], 'Discount Type',
                                     readonly=True, default='percent', states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate', readonly=True, states={'draft': [('readonly', False)]})
    discount_narration = fields.Char('Discount Narration', readonly=True, states={'draft': [('readonly', False)]})
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account',
                                  readonly=True, states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount', digits='Account',
                                   readonly=True, compute='_compute_amount',
                                   compute_sudo=True)
    amount_grand = fields.Float(string='Total', digits='Account',
                                store=True, readonly=True, compute='_compute_amount')
    amount_total = fields.Monetary(string='Net Total',
                                   store=True, readonly=True, compute='_compute_amount',
                                   inverse='_inverse_amount_total')

    @api.onchange('discount_rate', 'discount_type')
    def _onchange_amount_discount(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        sale_purchase_global_discount = self.env['ir.config_parameter'].sudo().get_param(
            'tis_sales_purchase_global_discount.sale_purchase_global_discount')

        if sale_purchase_global_discount == 'True':

            # sale_discount_account = self.env['ir.config_parameter'].sudo().get_param(
            #     'tis_sales_purchase_global_discount.def_discount_sales_account_id')
            # purchase_discount_account = self.env['ir.config_parameter'].sudo().get_param(
            #     'tis_sales_purchase_global_discount.def_discount_purchase_account_id')

            credit = 0.0
            debit = 0.0
            default_discount_account = False
            for vals in self:
                if vals.move_type in ('in_invoice', 'in_refund'):
                    default_discount_account = literal_eval(
                        ICPSudo.get_param('tis_sales_purchase_global_discount.def_discount_purchase_account_id',
                                          default='False'))
                elif vals.move_type in ('out_invoice', 'out_refund'):
                    default_discount_account = literal_eval(
                        ICPSudo.get_param('tis_sales_purchase_global_discount.def_discount_sales_account_id',
                                          default='False'))
                if vals.move_type in ('out_invoice', 'in_refund'):
                    credit = 0.0
                    debit = vals.amount_discount
                elif vals.move_type in ('in_invoice', 'out_refund'):
                    credit = vals.amount_discount
                    debit = 0.0

                existing_discount_line = vals.line_ids.filtered(
                    lambda x: x.account_id.id == default_discount_account)
                if vals.move_type in ('in_invoice', 'in_refund'):
                    existing_discount_line.credit = vals.amount_discount
                else:
                    existing_discount_line.debit = vals.amount_discount
                if vals.amount_discount > 0 and not existing_discount_line:
                    create_method = vals.env['account.move.line'].new or vals.env['account.move.line'].create
                    candidate = create_method({
                        'name': vals.payment_reference or '',
                        'debit': debit,
                        'credit': credit,
                        'quantity': 1,
                        'amount_currency': -vals.amount_discount,
                        'date_maturity': vals.invoice_date,
                        'move_id': vals.id,
                        'currency_id': vals.currency_id.id if vals.currency_id != vals.company_id.currency_id else False,
                        'account_id': default_discount_account,
                        'analytic_account_id': vals.analytic_id.id if vals.analytic_id else '',
                        'partner_id': vals.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True
                    })
                else:
                    existing_discount_line.credit = 0
                    existing_discount_line.debit = 0
                    self._onchange_invoice_line_ids()
                    self.line_ids -= existing_discount_line
                super(AccountMove, vals)._onchange_recompute_dynamic_lines()

    def _move_autocomplete_invoice_lines_values(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        sale_purchase_global_discount = self.env['ir.config_parameter'].sudo().get_param(
            'tis_sales_purchase_global_discount.sale_purchase_global_discount')

        if sale_purchase_global_discount == 'True':

            super(AccountMove, self)._move_autocomplete_invoice_lines_values()

            # sale_discount_account = self.env['ir.config_parameter'].sudo().get_param(
            #     'tis_sales_purchase_global_discount.def_discount_sales_account_id')
            # purchase_discount_account = self.env['ir.config_parameter'].sudo().get_param(
            #     'tis_sales_purchase_global_discount.def_discount_purchase_account_id')

            credit = 0.0
            debit = 0.0
            default_discount_account = False
            for vals in self:
                if vals.move_type in ('in_invoice', 'in_refund'):
                    default_discount_account = literal_eval(
                        ICPSudo.get_param('tis_sales_purchase_global_discount.def_discount_purchase_account_id',
                                          default='False'))
                elif vals.move_type in ('out_invoice', 'out_refund'):
                    default_discount_account = literal_eval(
                        ICPSudo.get_param('tis_sales_purchase_global_discount.def_discount_sales_account_id',
                                          default='False'))

                if vals.move_type in ('out_invoice', 'in_refund'):
                    credit = 0.0
                    debit = vals.amount_discount
                elif vals.move_type in ('in_invoice', 'out_refund'):
                    credit = vals.amount_discount
                    debit = 0.0

                if vals.amount_discount > 0:
                    create_method = vals.env['account.move.line'].new or vals.env['account.move.line'].create
                    candidate = create_method({
                        'name': vals.payment_reference or '',
                        'debit': debit,
                        'credit': credit,
                        'quantity': 1,
                        'amount_currency': -vals.amount_discount,
                        'date_maturity': vals.invoice_date,
                        'move_id': vals.id,
                        'currency_id': vals.currency_id.id if vals.currency_id != vals.company_id.currency_id else False,
                        'account_id': default_discount_account,
                        'analytic_account_id': vals.analytic_id.id if vals.analytic_id else '',
                        'partner_id': vals.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True
                    })
                self._recompute_dynamic_lines(recompute_all_taxes=True)
                values = self._convert_to_write(self._cache)
                values.pop('invoice_line_ids', None)
                return values
        else:
            return super(AccountMove, self)._move_autocomplete_invoice_lines_values()
