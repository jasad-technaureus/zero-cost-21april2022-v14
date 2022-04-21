# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import models, fields, api
import datetime
from ast import literal_eval


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_manual = fields.Boolean(string="Manual Rate", default=False)
    main_curr_rate = fields.Float(string="Main Currency Rate", digits=0)
    main_curr_rate_new = fields.Float(string="Main Currency Rate New", digits=0,
                                      compute='compute_main_currency_rate_new')
    is_diff_currency = fields.Boolean(string="Is Different currency", compute='is_different_currency', default=False,
                                      store=True)

    is_diff_currency_main = fields.Boolean(string="Is Different Main Currency", default=False,
                                           compute='is_different_currency', store=True)

    @api.depends('currency_id', 'is_manual')
    def is_different_currency(self):


        ICPSudo = self.env['ir.config_parameter'].sudo()

        allow_main_curr_rate = ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate')
        if self.currency_id:

            if self.currency_id != self.company_currency_id:

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

            invoice = self.env['account.move'].browse([self.id])
            if invoice.invoice_date:

                self._cr.execute(query, (invoice.invoice_date, self.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate_new = currency_rates.get(self.currency_id.id)
            elif invoice.date:

                self._cr.execute(query, (invoice.date, self.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())

                self.main_curr_rate_new = currency_rates.get(self.currency_id.id)

            else:

                self._cr.execute(query, (datetime.datetime.now().date(), self.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate_new = currency_rates.get(self.currency_id.id)

            if self.main_curr_rate != self.main_curr_rate_new:
                self.main_curr_rate = self.main_curr_rate_new
        else:
            self.main_curr_rate_new = self.main_curr_rate

    @api.onchange('date', 'currency_id')
    def _onchange_currency(self):

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

            invoice = self.env['account.move'].browse([self.id])
            if invoice.invoice_date:

                self._cr.execute(query, (invoice.invoice_date, self.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate = currency_rates.get(self.currency_id.id)
            elif invoice.date:

                self._cr.execute(query, (invoice.date, self.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())

                self.main_curr_rate = currency_rates.get(self.currency_id.id)


            else:

                self._cr.execute(query, (datetime.datetime.now().date(), self.company_id.id, self.currency_id.id))
                currency_rates = dict(self._cr.fetchall())
                self.main_curr_rate = currency_rates.get(self.currency_id.id)


        return super(AccountMove, self)._onchange_currency()

    def _recompute_tax_lines(self, recompute_tax_base_amount=False):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context

        return super(AccountMove, self)._recompute_tax_lines(recompute_tax_base_amount=recompute_tax_base_amount)

    def _recompute_cash_rounding_lines(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context

        return super(AccountMove, self)._recompute_cash_rounding_lines()

    def _inverse_amount_total(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context

        return super(AccountMove, self)._inverse_amount_total()

    def _compute_payments_widget_to_reconcile_info(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context

        return super(AccountMove, self)._compute_payments_widget_to_reconcile_info()

    @api.depends('line_ids.price_subtotal', 'line_ids.tax_base_amount', 'line_ids.tax_line_id', 'partner_id',
                 'currency_id')
    def _compute_invoice_taxes_by_group(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context

        return super(AccountMove, self)._compute_invoice_taxes_by_group()

    def _move_autocomplete_invoice_lines_values(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context

        return super(AccountMove, self)._move_autocomplete_invoice_lines_values()

    def update_price_rate(self):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        if is_rate_change and self.is_manual:
            self.with_context(check_move_validity=False)._onchange_currency()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):

        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.move_id.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.move_id.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context
        return super(AccountMoveLine, self)._get_fields_onchange_subtotal_model(price_subtotal=price_subtotal,
                                                                                move_type=move_type, currency=currency,
                                                                                company=company, date=date)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.move_id.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.move_id.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context

        return super(AccountMoveLine, self)._onchange_product_id()

    @api.onchange('product_uom_id')
    def _onchange_uom_id(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.move_id.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.move_id.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context
        return super(AccountMoveLine, self)._onchange_uom_id()

    @api.onchange('amount_currency')
    def _onchange_amount_currency(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.move_id.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.move_id.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context
        return super(AccountMoveLine, self)._onchange_amount_currency()

    @api.onchange('currency_id')
    def _onchange_currency(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_rate_change = literal_eval(
            ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
                              default='False'))
        main_curr = self.currency_id.id
        if is_rate_change and self.move_id.is_manual:
            context = self._context.copy()
            context.update({'main_currency_rate': self.move_id.main_curr_rate, 'main_curr': main_curr})
            self.env.context = context
        return super(AccountMoveLine, self)._onchange_currency()

    # def _prepare_reconciliation_partials(self):
    #     for data in self:
    #
    #         move = self.env['account.move'].browse(data.move_id.id)
    #
    #
    #         ICPSudo = data.env['ir.config_parameter'].sudo()
    #         is_rate_change = literal_eval(
    #             ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
    #                               default='False'))
    #         main_curr = data.currency_id.id
    #         if is_rate_change and data.move_id.is_manual:
    #             context = data._context.copy()
    #             context.update({'main_currency_rate': data.move_id.main_curr_rate, 'main_curr': main_curr})
    #             data.env.context = context
    #     return super(AccountMoveLine, self)._prepare_reconciliation_partials()

    # def _create_exchange_difference_move(self):
    #     for data in self:
    #
    #         ICPSudo = data.env['ir.config_parameter'].sudo()
    #         is_rate_change = literal_eval(
    #             ICPSudo.get_param('zero_currency_rate.allow_main_curr_rate',
    #                               default='False'))
    #         main_curr = data.currency_id.id
    #         if is_rate_change and data.move_id.is_manual:
    #             context = data._context.copy()
    #             context.update({'main_currency_rate': data.move_id.main_curr_rate, 'main_curr': main_curr})
    #             data.env.context = context
    #     return super(AccountMoveLine, self)._create_exchange_difference_move()
