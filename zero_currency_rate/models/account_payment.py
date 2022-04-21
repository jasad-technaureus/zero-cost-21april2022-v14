# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields, api
import datetime
from ast import literal_eval


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_manual = fields.Boolean(string="Manual Rate", default=False)
    main_curr_rate = fields.Float(string="Main Currency Rate", digits=0)
    is_diff_currency = fields.Boolean(string="Is Different currency", compute='is_different_currency', default=False,
                                      store=True)
    main_curr_rate_new = fields.Float(string="Main Currency Rate New", digits=0,
                                      compute='compute_main_currency_rate_new')
    is_diff_currency_main = fields.Boolean(string="Is Different Main Currency", default=False,
                                           compute='is_different_currency', store=True)

    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        if 'main_curr_rate' in vals:
            self.move_id.write({
                'is_manual': self.is_manual,
                'is_diff_currency': self.is_diff_currency,
                'main_curr_rate': self.main_curr_rate
            })
        return res

    @api.depends('date', 'currency_id')
    def compute_main_currency_rate_new(self):
        if not self.is_manual:
            self.env['res.currency.rate'].flush(['rate', 'currency_id', 'company_id', 'name'])
            query = """SELECT c.id,
                                       COALESCE((SELECT r.main_currency_rate FROM res_currency_rate r
                                       WHERE r.currency_id = c.id AND r.name <= %s
                                       AND (r.company_id IS NULL OR r.company_id = %s)
                                       ORDER BY r.company_id, r.name DESC
                                       LIMIT 1), 1.0) AS rate
                                       FROM res_currency c
                                       WHERE c.id = %s"""

            if self.invoice_date:

                self._cr.execute(query, (self.invoice_date, self.journal_id.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate_new = currency_rates.get(self.currency_id.id)
            elif self.date:

                self._cr.execute(query, (self.date, self.journal_id.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())

                self.main_curr_rate_new = currency_rates.get(self.currency_id.id)

            else:

                self._cr.execute(query, (datetime.datetime.now().date(), self.journal_id.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate_new = currency_rates.get(self.currency_id.id)

            if self.main_curr_rate != self.main_curr_rate_new:
                self.main_curr_rate = self.main_curr_rate_new
        else:
            self.main_curr_rate_new = self.main_curr_rate

    @api.model_create_multi
    def create(self, vals_list):
        self.update_price_rate()
        return super(AccountPayment, self).create(vals_list)

    def update_price_rate(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        if is_rate_change and self.is_manual:
            self.move_id.write({
                'is_manual': self.is_manual,
                'is_diff_currency': self.is_diff_currency,
                'main_curr_rate': self.main_curr_rate

            })
            self.move_id.with_context(check_move_validity=False)._onchange_currency()

    @api.depends('currency_id', 'journal_id')
    def is_different_currency(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()

        allow_main_curr_rate = ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate')
        if self.currency_id:
            if self.currency_id != self.journal_id.company_id.currency_id:

                self.is_diff_currency_main = True
                if allow_main_curr_rate == 'True':
                    self.is_diff_currency = True
                else:
                    self.is_diff_currency = False
            else:

                self.is_manual = False
                self.is_diff_currency = False
                self.is_diff_currency_main = False

        else:
            self.is_diff_currency = False
            self.is_diff_currency_main = False

    @api.onchange('date', 'currency_id')
    def onchange_payment_currency(self):

        if self.currency_id:
            self.is_different_currency()
            self.env['res.currency.rate'].flush(['rate', 'currency_id', 'company_id', 'name'])
            query = """SELECT c.id,
                        COALESCE((SELECT r.main_currency_rate FROM res_currency_rate r
                        WHERE r.currency_id = c.id AND r.name <= %s
                        AND (r.company_id IS NULL OR r.company_id = %s)
                        ORDER BY r.company_id, r.name DESC
                        LIMIT 1), 1.0) AS rate
                        FROM res_currency c
                        WHERE c.id = %s"""
            payment = self.env['account.payment'].browse([self.id])
            if payment.date:
                self._cr.execute(query,
                                 (payment.date, self.journal_id.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate = currency_rates.get(self.currency_id.id)
            else:
                self._cr.execute(query,
                                 (datetime.datetime.now().date(), self.journal_id.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate = currency_rates.get(self.currency_id.id)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id

        if is_rate_change and self.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': main_curr})

            self.env.context = context

        return super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)


# class AccountPaymentRegister(models.TransientModel):
#     _inherit = 'account.payment.register'
#
#     def _create_payment_vals_from_wizard(self):
#         res = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
#         if self._context.get('active_model') == 'account.move':
#             lines = self.env['account.move'].browse(self._context.get('active_ids', []))
#             print("ORIGINAL MOVE", lines, lines.is_manual, lines.is_diff_currency,lines.main_curr_rate_new, lines.is_diff_currency_main)
#             # res['is_manual'] = lines.is_manual
#             # res['is_diff_currency'] = lines.is_diff_currency
#             # res['main_curr_rate_new'] = lines.main_curr_rate_new
#             # res['is_diff_currency_main'] = lines.is_diff_currency_main
#         return res

