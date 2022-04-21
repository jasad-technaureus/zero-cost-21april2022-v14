# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    vat_amount = fields.Float(string='VAT Amount', compute='_compute_vat_amount')

    unit_price_with_vat = fields.Float(string='Unit Price With VAT')

    @api.depends('tax_ids')
    def _compute_vat_amount(self):
        for vals in self:
            vals.vat_amount = vals.price_total - vals.price_subtotal
