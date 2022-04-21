# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def get_invoice_number(self, name):
        order = self.env['pos.order'].search([('pos_reference', '=', name)])
        invoice = self.env['account.move'].search([('payment_reference', '=', order.name)])
        if invoice:
            return invoice.name
