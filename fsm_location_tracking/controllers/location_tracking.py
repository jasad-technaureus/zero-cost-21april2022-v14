# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import json
import logging
import werkzeug

from odoo import http, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError
from odoo.http import request

import datetime

_logger = logging.getLogger(__name__)


class AuthSignupHome(Home):

    @http.route('/get_location_lati_longi', type='http', auth='public', website=True, sitemap=False)
    def get_selected_heard_about_us(self, *args, **value):
        task_id = value.get('task_id')
        current_task = request.env['project.task'].sudo().browse(int(task_id))
        latitude = value.get('latitude')
        longitude = value.get('longitude')
        current_task.task_latitude_fsm = latitude
        current_task.task_longitude_fsm = longitude
        return "ok"