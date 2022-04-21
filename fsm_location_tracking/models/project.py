# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import os
from odoo import fields, models, api, _
from odoo.http import request


class Task(models.Model):
    _inherit = "project.task"

    partner_latitude_fsm = fields.Float(digits=(16, 5), string='Partner Latitude', compute='_compute_partner_latitude',
                                        store=False)
    partner_longitude_fsm = fields.Float(digits=(16, 5), string='Partner Longitude',
                                         compute='_compute_partner_longitude', store=False)
    task_latitude_fsm = fields.Float(digits=(16, 5), string='Task Latitude')
    task_longitude_fsm = fields.Float(digits=(16, 5), string='Task Longitude')
    onsite = fields.Boolean("Onsite", compute='_compute_task_onsite')
    marked_as_done_fsm = fields.Boolean("Done")

    @api.depends('partner_id')
    def _compute_partner_latitude(self):
        if not self.env.user.has_group('fsm_location_tracking.group_fsm_track_location'):
            self.partner_latitude_fsm = 0
        else:
            self.partner_latitude_fsm = 0
            for rec in self:
                partner = rec.partner_id
                if partner:
                    partner_lati = partner.partner_latitude
                    if partner_lati:
                        rec.partner_latitude_fsm = partner_lati
                    else:
                        rec.partner_latitude_fsm = 0.0

    @api.depends('partner_id')
    def _compute_partner_longitude(self):
        if not self.env.user.has_group('fsm_location_tracking.group_fsm_track_location'):
            self.partner_longitude_fsm = 0
        else:
            self.partner_longitude_fsm = 0
            for rec in self:
                partner = rec.partner_id
                if partner:
                    partner_long = partner.partner_longitude
                    if partner_long:
                        rec.partner_longitude_fsm = partner_long
                    else:
                        rec.partner_longitude_fsm = 0.0

    @api.depends('task_latitude_fsm', 'task_longitude_fsm')
    def _compute_task_onsite(self):
        self.onsite = False
        if self.env.user.has_group('fsm_location_tracking.group_fsm_track_location'):
            lati = self.task_latitude_fsm
            longi = self.task_longitude_fsm
            partner_lati = self.partner_latitude_fsm
            partner_long = self.partner_longitude_fsm
            from math import radians, cos, sin, asin, sqrt

            lat1, long1, lat2, long2 = map(radians,
                                           [lati, longi, partner_lati,
                                            partner_long])
            # haversine formula
            dlon = long2 - long1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            # Radius of earth in kilometers is 6371
            km_distance = 6371 * c
            print("km", km_distance)
            ICPSudo = self.env['ir.config_parameter'].sudo().get_param('fsm_location_tracking.fsm_distance_km')
            distance_set = ICPSudo
            if distance_set:
                if self.task_latitude_fsm == partner_lati and self.task_longitude_fsm == partner_long:
                    self.onsite = True
                elif km_distance <= int(distance_set):
                    self.onsite = True
                else:
                    self.onsite = False

