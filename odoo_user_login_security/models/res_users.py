# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from collections import defaultdict
from contextlib import contextmanager
from datetime import timedelta
from logging import getLogger

from odoo import _,api,fields,models,SUPERUSER_ID
from odoo.exceptions import AccessDenied
from odoo.http import request


_logger = getLogger(__name__)


class ResUsers(models.Model):
	_inherit = 'res.users'

	session_ids = fields.One2many(
		comodel_name='session.session',
		inverse_name='user_id',
		string='Sessions',
	)

	login_failure_count = fields.Integer(default=0)
	last_login_attempt = fields.Datetime(default=fields.datetime.min)

	def write(self,vals):
		if 'password' in vals:
			vals['last_password_reset'] = fields.datetime.utcnow()
			for rec in self:
				rec.terminate_sessions()
		return super().write(vals)

	def terminate_sessions(self):
		self.env['session.session'].search([('user_id','in',self.ids)]).terminate()

	def recommend_password_update(self):
		self.ensure_one()
		self.env['mail.message'].create(
			 {
				'message_type': 'notification',
				'subtype_id': self.env.ref('mail.mt_comment').id,
				'author_id': self.sudo().browse(SUPERUSER_ID).partner_id.id,
				'subject': 'Password too old',
				'body': 'It is recommended to update password.',
				'partner_ids': [(4, self.partner_id.id)],
			}
		)

	def _check_credentials(self, password, env):
		with self._assert_can_auth_user():
			super()._check_credentials(password, env)

	@contextmanager
	def _assert_can_auth_user(self):
		if not request:
			yield
			return

		get_param = self.env['ir.config_parameter'].sudo().get_param
		min_failures = int(get_param('odoo_user_login_security.login_cooldown_after', 5))
		delay = int(get_param('odoo_user_login_security.login_cooldown_duration', 60))

		failures = self.login_failure_count
		previous = self.last_login_attempt

		if failures >= min_failures and fields.datetime.now() < previous+timedelta(seconds=delay):
			_logger.warn(
				f'Login attempt ignored for {self.name} on {self.env.cr.dbname}:'
				f'{failures} failures since last success, last failure at {previous}.'
			)
			raise AccessDenied(_('Too many login failures, please wait a bit before trying again.'))

		try:
			yield
		except AccessDenied:
			self.sudo().write(
				{
					'login_failure_count': failures+1,
					'last_login_attempt': fields.datetime.now(),
				}
			)
			raise
		else:
			self.sudo().write(
				{
					'login_failure_count': False,
					'last_login_attempt': False,
				}
			)
