# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    group_fsm_track_location = fields.Boolean("Track Location",
                                        help="Get the location for each task when it is marked as done",
                                        implied_group='fsm_location_tracking.group_fsm_track_location')
    fsm_distance_km = fields.Integer(string="Nearest Distance", help="Distance in KM considered as nearest")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("fsm_location_tracking.fsm_distance_km",
                          self.fsm_distance_km)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        fsm_distance_km = ICPSudo.get_param('fsm_location_tracking.fsm_distance_km')
        res.update(
            fsm_distance_km=fsm_distance_km,
        )
        return res
