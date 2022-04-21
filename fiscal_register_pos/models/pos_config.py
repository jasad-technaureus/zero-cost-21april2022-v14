# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    fiscal_device_id = fields.Many2one('fiscal.devices', string='Fiscal Device')
    max_amount = fields.Monetary(string='Maximium Amount', currency_field='currency_id')
    mxm_amount_invoice = fields.Monetary(string='Maximum Amount Invoice', currency_field='currency_id')
