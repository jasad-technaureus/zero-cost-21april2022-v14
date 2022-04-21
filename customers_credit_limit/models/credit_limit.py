# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.


from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_currency_id = fields.Many2one('res.currency', string='Company Currency',
                                          default=lambda self: self.env.company.currency_id)
    warning_limit = fields.Monetary(string='Warning Limit')
    blocking_limit = fields.Monetary(string='Blocking Limit')

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        for order in self.sale_order_ids:
            order.onchange_order_line()
        for invoice in self.invoice_ids:
            invoice.onchange_invoice_line_ids()
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_cred_warning = fields.Boolean(default=False)
    partner_cred_blocking = fields.Boolean(default=False)
    warning_limit = fields.Monetary(related='partner_id.warning_limit')
    blocking_limit = fields.Monetary(related='partner_id.blocking_limit')
    partner_total_credit = fields.Monetary(related='partner_id.credit')
    total_credit_amount = fields.Monetary(compute='compute_partner_credit')
    company_currency_id = fields.Many2one('res.currency', string='Company Currency',
                                          default=lambda self: self.env.company.currency_id)

    @api.onchange('order_line')
    def onchange_order_line(self):
        self.compute_partner_credit()
        converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                           self.company_id,
                                                           self.date_order, round=True)
        if self.partner_id.blocking_limit > 0 or self.partner_id.warning_limit > 0:
            amount = converted_total_amount + self.partner_id.credit
            if amount >= self.partner_id.blocking_limit and self.partner_id.blocking_limit > 0:
                self.partner_cred_blocking = True
                self.partner_cred_warning = False
            elif amount >= self.partner_id.warning_limit and self.partner_id.warning_limit > 0:
                self.partner_cred_warning = True
                self.partner_cred_blocking = False
            else:
                self.partner_cred_warning = False
                self.partner_cred_blocking = False
        else:
            self.partner_cred_warning = False
            self.partner_cred_blocking = False

    def compute_partner_credit(self):
        converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                           self.company_id,
                                                           self.date_order, round=True)
        self.total_credit_amount = self.partner_id.credit + converted_total_amount

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(SaleOrder, self).onchange_partner_id()
        self.onchange_order_line()
        converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                           self.company_id,
                                                           self.date_order, round=True)
        if self.partner_id.blocking_limit > 0 or self.partner_id.warning_limit > 0:
            if self.order_line:
                amount = converted_total_amount + self.partner_id.credit
                if amount > self.partner_id.blocking_limit and self.partner_id.blocking_limit > 0:
                    self.partner_cred_blocking = True
                    self.partner_cred_warning = False
                elif amount >= self.partner_id.warning_limit and self.warning_limit > 0:
                    self.partner_cred_warning = True
                    self.partner_cred_blocking = False
                else:
                    self.partner_cred_warning = False
                    self.partner_cred_blocking = False

            partner_credit = "{:.2f}".format(self.partner_id.credit)
            warning_limit = "{:.2f}".format(self.partner_id.warning_limit)
            blocking_limit = "{:.2f}".format(self.partner_id.blocking_limit)
            if self.partner_id.credit > 0 and self.partner_id.credit >= self.partner_id.blocking_limit and self.partner_id.blocking_limit > 0:
                if self.company_currency_id.position == 'before':
                    return {
                        'warning': {'title': "Warning",
                                    'message': "The customer total receivable is " + self.company_currency_id.symbol + str(
                                        partner_credit) + '.' + " This customer has exceeded his blocking limit " + self.company_currency_id.symbol + str(
                                        blocking_limit) + " !"},
                    }
                if self.company_currency_id.position == 'after':
                    return {
                        'warning': {'title': "Warning",
                                    'message': "The customer total receivable is " + str(
                                        partner_credit) + self.company_currency_id.symbol + '.' + " This customer has exceeded his blocking limit " + str(
                                        blocking_limit) + self.company_currency_id.symbol + " !"},
                    }

            elif self.partner_id.credit > 0 and self.partner_id.credit >= self.partner_id.warning_limit and self.partner_id.warning_limit > 0:
                if self.company_currency_id.position == 'before':
                    return {
                        'warning': {'title': "Warning",
                                    'message': "The customer total receivable is " + self.company_currency_id.symbol + str(
                                        partner_credit) + '.' + " This customer has exceeded his warning limit " + self.company_currency_id.symbol + str(
                                        warning_limit) + " !"},
                    }
                if self.company_currency_id.position == 'after':
                    return {
                        'warning': {'title': "Warning",
                                    'message': "The customer total receivable is " + str(
                                        partner_credit) + self.company_currency_id.symbol + '.' + " This customer has exceeded his warning limit " + str(
                                        warning_limit) + self.company_currency_id.symbol + " !"},
                    }
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                           self.company_id,
                                                           self.date_order, round=True)
        if self.partner_id.blocking_limit > 0 or self.partner_id.warning_limit > 0:
            amount = converted_total_amount + self.partner_id.credit
            context = self.env.context.copy()
            context.update(
                {'default_partner_total_credit': self.partner_id.credit, 'default_total_credit_amount': amount,
                 'default_warning_limit': self.partner_id.warning_limit,
                 'default_blocking_limit': self.partner_id.blocking_limit,
                 'default_currency_id': self.company_id.currency_id.id})
            if amount >= self.partner_id.blocking_limit and self.partner_id.blocking_limit > 0:
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'credit.blocking.wizard',
                    'views': [(False, 'form')],

                    'target': 'new',
                    'context': context}
            elif amount >= self.partner_id.warning_limit and self.partner_id.warning_limit > 0:
                return {
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'credit.warning.wizard',
                    'views': [(False, 'form')],

                    'target': 'new',
                    'context': context,
                }
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_cred_warning = fields.Boolean(default=False)
    partner_cred_blocking = fields.Boolean(default=False)
    warning_limit = fields.Monetary(related='partner_id.warning_limit')
    blocking_limit = fields.Monetary(related='partner_id.blocking_limit')
    partner_total_credit = fields.Monetary(related='partner_id.credit')
    total_credit_amount = fields.Monetary(compute='compute_partner_credit')
    company_currency_id = fields.Many2one('res.currency', string='Company Currency',
                                          default=lambda self: self.env.company.currency_id)

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        if vals.get('move_type') == 'out_invoice':  # if duplicating an invoice
            res.onchange_invoice_line_ids()
        if vals.get('invoice_origin') and vals.get('move_type') == 'out_invoice':
            if res.partner_id.blocking_limit > 0 or res.partner_id.warning_limit > 0:
                amount = res.amount_total + res.partner_id.credit
                if amount >= res.partner_id.blocking_limit and res.partner_id.blocking_limit > 0:
                    res.partner_cred_blocking = True
                    res.partner_cred_warning = False
                elif amount >= res.partner_id.warning_limit and res.partner_id.warning_limit > 0:
                    res.partner_cred_warning = True
                    res.partner_cred_blocking = False
        return res

    @api.onchange('invoice_line_ids')
    def onchange_invoice_line_ids(self):
        if self.move_type == 'out_invoice':
            self.compute_partner_credit()
            converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                               self.company_id,
                                                               self.date, round=True)
            if self.partner_id.blocking_limit > 0 or self.partner_id.warning_limit > 0:
                amount = converted_total_amount + self.partner_id.credit
                if amount >= self.partner_id.blocking_limit and self.partner_id.blocking_limit > 0:
                    self.partner_cred_blocking = True
                    self.partner_cred_warning = False
                elif amount >= self.partner_id.warning_limit and self.partner_id.warning_limit > 0:
                    self.partner_cred_warning = True
                    self.partner_cred_blocking = False
                else:
                    self.partner_cred_warning = False
                    self.partner_cred_blocking = False
            else:
                self.partner_cred_warning = False
                self.partner_cred_blocking = False

    def compute_partner_credit(self):
        converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                           self.company_id,
                                                           self.date, round=True)
        self.total_credit_amount = self.partner_id.credit + converted_total_amount

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.move_type == 'out_invoice':
            self.onchange_invoice_line_ids()
            converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                               self.company_id,
                                                               self.date, round=True)
            if self.partner_id.blocking_limit > 0 or self.partner_id.warning_limit > 0:
                if self.invoice_line_ids:
                    amount = converted_total_amount + self.partner_id.credit
                    if amount > self.partner_id.blocking_limit:
                        self.partner_cred_blocking = True
                        self.partner_cred_warning = False
                    elif amount >= self.warning_limit:
                        self.partner_cred_warning = True
                        self.partner_cred_blocking = False
                    else:
                        self.partner_cred_warning = False
                        self.partner_cred_blocking = False
                partner_credit = "{:.2f}".format(self.partner_id.credit)
                warning_limit = "{:.2f}".format(self.partner_id.warning_limit)
                blocking_limit = "{:.2f}".format(self.partner_id.blocking_limit)
                if self.move_type == 'out_invoice':
                    if self.partner_id.credit > 0 and self.partner_id.credit >= self.partner_id.blocking_limit and self.partner_id.blocking_limit > 0:
                        if self.company_currency_id.position == 'before':
                            return {
                                'warning': {'title': "Warning",
                                            'message': "The customer total receivable is " + self.company_currency_id.symbol + str(
                                                partner_credit) + '.' + " This customer has exceeded his blocking limit " + self.company_currency_id.symbol + str(
                                                blocking_limit) + " !"},
                            }
                        if self.company_currency_id.position == 'after':
                            return {
                                'warning': {'title': "Warning",
                                            'message': "The customer total receivable is " + str(
                                                partner_credit) + self.company_currency_id.symbol + '.' + " This customer has exceeded his blocking limit " + str(
                                                blocking_limit) + self.company_currency_id.symbol + " !"},
                            }

                    elif self.partner_id.credit > 0 and self.partner_id.credit >= self.partner_id.warning_limit and self.partner_id.warning_limit > 0:
                        if self.company_currency_id.position == 'before':
                            return {
                                'warning': {'title': "Warning",
                                            'message': "The customer total receivable is " + self.company_currency_id.symbol + str(
                                                partner_credit) + '.' + " This customer has exceeded his warning limit " + self.company_currency_id.symbol + str(
                                                warning_limit) + " !"},
                            }
                        if self.company_currency_id.position == 'after':
                            return {
                                'warning': {'title': "Warning",
                                            'message': "The customer total receivable is " + str(
                                                partner_credit) + self.company_currency_id.symbol + '.' + " This customer has exceeded his warning limit " + str(
                                                warning_limit) + self.company_currency_id.symbol + " !"},
                            }

    def action_post(self):
        if self.move_type == 'out_invoice':
            converted_total_amount = self.currency_id._convert(self.amount_total, self.env.company.currency_id,
                                                               self.company_id,
                                                               self.date, round=True)
            if self.partner_id.blocking_limit > 0 or self.partner_id.warning_limit > 0:
                amount = converted_total_amount + self.partner_id.credit
                context = self.env.context.copy()
                context.update(
                    {'default_partner_total_credit': self.partner_id.credit, 'default_total_credit_amount': amount,
                     'default_warning_limit': self.partner_id.warning_limit,
                     'default_blocking_limit': self.partner_id.blocking_limit,
                     'inv_id': self.id,
                     'default_currency_id': self.company_id.currency_id.id})
                if self.move_type == 'out_invoice':
                    if amount >= self.partner_id.blocking_limit and self.partner_id.blocking_limit > 0:
                        view_id = self.env.ref('customers_credit_limit.credit_limit_blocking_view_wizard')
                        return {
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'credit.blocking.wizard',
                            'views': [(False, 'form')],
                            'view_id': view_id.id,
                            'target': 'new',
                            'context': context}
                    elif amount >= self.partner_id.warning_limit and self.partner_id.warning_limit > 0:
                        view_id = self.env.ref('customers_credit_limit.credit_limit_warning_view_wizard')
                        return {
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'credit.warning.wizard',
                            'views': [(False, 'form')],
                            'view_id': view_id.id,
                            'target': 'new',
                            'context': context,
                        }

                return self._post(soft=False)
            else:
                return super(AccountMove, self).action_post()
        else:
            return super(AccountMove, self).action_post()
