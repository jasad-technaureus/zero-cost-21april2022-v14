# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd. - ©
# Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
from odoo import api, fields, models
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def_discount_sales_account_id = fields.Many2one('account.account', string='Default Sale Discount Account',

                                                    readonly=False)
    def_discount_purchase_account_id = fields.Many2one('account.account', string='Default Purchase Discount Account',
                                                       readonly=False)
    sale_purchase_global_discount = fields.Boolean(string="Enable Sale Purchase Global Discount", default=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        sale_purchase_global_discount = ICPSudo.get_param(
            'tis_sales_purchase_global_discount.sale_purchase_global_discount')
        def_discount_sales_account_id = literal_eval(
            ICPSudo.get_param('tis_sales_purchase_global_discount.def_discount_sales_account_id', default='False'))
        def_discount_purchase_account_id = literal_eval(
            ICPSudo.get_param('tis_sales_purchase_global_discount.def_discount_purchase_account_id', default='False'))
        if def_discount_sales_account_id and not self.env['account.account'].browse(
                def_discount_sales_account_id).exists():
            def_discount_sales_account_id = False
        if def_discount_purchase_account_id and not self.env['account.account'].browse(
                def_discount_purchase_account_id).exists():
            def_discount_purchase_account_id = False
        res.update(
            def_discount_sales_account_id=def_discount_sales_account_id,
            def_discount_purchase_account_id=def_discount_purchase_account_id,
            sale_purchase_global_discount=sale_purchase_global_discount
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("tis_sales_purchase_global_discount.def_discount_sales_account_id",
                          self.def_discount_sales_account_id.id)
        ICPSudo.set_param("tis_sales_purchase_global_discount.def_discount_purchase_account_id",
                          self.def_discount_purchase_account_id.id)
        ICPSudo.set_param("tis_sales_purchase_global_discount.sale_purchase_global_discount",
                          self.sale_purchase_global_discount)
