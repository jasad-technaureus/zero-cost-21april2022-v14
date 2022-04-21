# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def_fiscal_device_id = fields.Many2one('fiscal.devices', string="Default Fiscal Printer", config_parameter='fiscal_register_accounting.def_fiscal_device_id')
    max_amount_move = fields.Float(string='Maximium Amount', config_parameter='fiscal_register_accounting.max_amount_move')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("fiscal_register_accounting.def_fiscal_device_id",
                          self.def_fiscal_device_id.id)


