# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    operator_code = fields.Char(string='Operator Code')
    business_unit_code = fields.Char(string='Business Unit Code')
    invoice_type = fields.Selection([('cash', 'CASH'),
                                     ('noncash', 'NONCASH')],
                                    string='Default Invoice Type',
                                    default='noncash')
