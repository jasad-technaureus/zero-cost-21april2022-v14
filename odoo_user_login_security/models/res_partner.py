# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from datetime import datetime, timedelta
from logging import getLogger

from odoo import api,fields,models,exceptions

UTC_NOW = datetime.utcnow()


class ResPartner(models.Model):
	_inherit = 'res.partner'

	password_reset_attempt_count = fields.Integer(default=0)
	last_password_reset_attempt  = fields.Datetime()
	last_password_reset          = fields.Datetime(default=lambda self: self.create_date)

	def signup_prepare(self, signup_type="reset", expiration=False):
		if not self._context.get('uid') and not self._context.get('active_model'):
			self.update_password_reset_attempt_count()
		if expiration:
			expiration_hours = self.env['ir.config_parameter'].sudo().get_param(
				'odoo_user_login_security.password_reset_attempt_expiration',
			)
			if expiration_hours:
				expiration = UTC_NOW + timedelta(hours=int(expiration_hours))
		return super(ResPartner, self).signup_prepare(signup_type, expiration)

	def update_password_reset_attempt_count(self,reset=False):
		get_param = self.env['ir.config_parameter'].sudo().get_param
		for rec in self:
			if reset:
				rec.password_reset_attempt_count = 0
				return

			password_reset_attempt_gap = get_param('odoo_user_login_security.password_reset_attempt_gap')
			if password_reset_attempt_gap:
				min_valid_timestamp = fields.date_utils.relativedelta(
					seconds=int(password_reset_attempt_gap)
				)
				min_valid_timestamp = rec.last_password_reset_attempt + min_valid_timestamp
				if min_valid_timestamp > UTC_NOW:
					raise exceptions.UserError('Wait a bit to try again.')

			password_reset_attempt_limit = int(
				get_param('odoo_user_login_security.password_reset_attempt_limit')
			)
			if password_reset_attempt_limit:
				if rec.password_reset_attempt_count >= password_reset_attempt_limit:
					raise exceptions.UserError(
						'No more attempt to reset password permitted.'
						'Contact administrator.'
					)
				else:
					hour_later = (rec.last_password_reset_attempt or rec.create_date) + timedelta(hours=1)
					if UTC_NOW > hour_later:
						rec.password_reset_attempt_count = 0
					rec.password_reset_attempt_count += 1
			rec.last_password_reset_attempt = UTC_NOW
