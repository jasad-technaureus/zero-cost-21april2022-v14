# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import models, fields, api


class CreditLimitWizard(models.Model):
    _name = 'credit.warning.wizard'
    _description = 'Wizard to show credit limit warning'

    currency_id = fields.Many2one('res.currency', string='Currency Id')
    partner_total_credit = fields.Monetary(string="Partner Total Credit", currency_field='currency_id')
    warning_limit = fields.Monetary(string='Warning Limit', currency_field='currency_id')
    blocking_limit = fields.Monetary(string='Blocking Limit', currency_field='currency_id')
    total_credit_amount = fields.Monetary(string='Total Credit Limit', currency_field='currency_id')

    def inv_ok(self):
        inv_id = self._context['inv_id']
        inv_data = self.env['account.move'].browse(inv_id)
        inv_data._post()


class CreditBlockingWizard(models.Model):
    _name = 'credit.blocking.wizard'
    _description = 'Wizard to show credit limit warning'

    currency_id = fields.Many2one('res.currency', string='Currency Id')
    partner_total_credit = fields.Monetary(string="Partner Total Credit", currency_field='currency_id')
    warning_limit = fields.Monetary(string='Warning Limit', currency_field='currency_id')
    blocking_limit = fields.Monetary(string='Blocking Limit', currency_field='currency_id')
    total_credit_amount = fields.Monetary(string='Total Credit Limit', currency_field='currency_id')

    def blocking_ok(self):
        inv_id = self._context['inv_id']
