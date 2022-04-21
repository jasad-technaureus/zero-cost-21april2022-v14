# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    automatic_cost_adjustment = fields.Boolean(string='Automatic Cost Adjustments')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        automatic_cost_adjustment = ICPSudo.get_param(
            'cost_adjustment.automatic_cost_adjustment')
        res.update(
            automatic_cost_adjustment=automatic_cost_adjustment
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        ICPSudo.set_param("cost_adjustment.automatic_cost_adjustment",
                          self.automatic_cost_adjustment)
