# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_main_curr_rate = fields.Boolean(string='Allow Main Currency Rate Feature',
                                          config_parameter='zero_currency_rate.allow_main_curr_rate', default=False)

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("zero_currency_rate.allow_main_curr_rate",
                          self.allow_main_curr_rate)
