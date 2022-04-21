# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    account_def_discount_sales_account_id = fields.Many2one('account.account', string='Default Discount Account')
    account_def_discount_purchase_account_id = fields.Many2one('account.account', string='Default Discount Account')
