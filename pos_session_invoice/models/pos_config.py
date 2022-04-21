# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class PosConfig(models.Model):
    _inherit = 'pos.config'

    customer_invoice = fields.Boolean(string='Customer Invoice', default=False)
    inv_partner_id = fields.Many2one('res.partner', string='Customer')
