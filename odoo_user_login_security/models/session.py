# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from logging import getLogger
from os.path import getmtime
from requests import get
from time import time

from odoo import api, fields, models
from odoo.http import request, root
from odoo.tools._vendor import sessions


GEOIP_API_URL = 'https://freegeoip.app/json/'
_logger = getLogger(__name__)


class UserSession(models.Model):
	_name        = 'session.session'
	_description = 'Session'
	_rec_name    = 'user_id'
	_order       = 'active desc,date_logout desc,date_login desc'


	def _compute_duration(self):
		for rec in self:
			if rec.date_logout:
				rec.duration = rec.date_logout - rec.date_login

	def _compute_if_current(self):
		for rec in self:
			rec.is_current = rec.session_id == request.session.sid and rec.user_id == request.env.user and rec.active

	@api.depends('ip')
	def _compute_country_id(self):
		for rec in self:
			url = f'{GEOIP_API_URL}{rec.ip}'
			try:
				response = get(url)
				if response.ok:
					code = response.json().get('country_code')
					if code:
						self.env.cr.execute("SELECT id FROM res_country WHERE code=%s", [code])
						[rec.country_id] = self.env.cr.fetchone()
			except Exception:
				_logger.warning('Failed to call geo-ip api for %s',url)

	def _compute_last_activity_on(self):
		for rec in self:
			if rec.active:
				try:
					rec.last_activity_on = getmtime(root.session_store.get_session_filename(rec.session_id))
				except FileNotFoundError:
					rec.last_activity_on = False
			else:
				rec.last_activity_on = False


	is_current = fields.Boolean(compute=_compute_if_current)
	active     = fields.Boolean('Logged',required=True,index=True)
	session_id = fields.Char('Session ID',size=100)
	ip         = fields.Char('Remote IP',size=15)
	platform   = fields.Selection(
		selection=[
			('android','Android'),
			('chromeos','ChromeOS'),
			('iphone','iPhone'),
			('ipad','iPad'),
			('macos','MacOS'),
			('windows','Windows'),
			('linux','Linux'),
			('other','Other Platforms'),
		],
		default='other',
	)
	browser = fields.Selection(
		selection=[
			('chrome','Google Chrome'),
			('edge','Microsoft Edge'),
			('firefox','Mozzila Firefox'),
			('msie','Internet Explorer'),
			('opera','Opera'),
			('safari','Safari'),
			('other','Other Browsers'),
		],
		default='other',
	)
	browser_version = fields.Char()
	user_agent      = fields.Char()
	date_login      = fields.Datetime('Login',required=True)
	date_logout     = fields.Datetime('Logout',inverse=_compute_duration)
	duration        = fields.Char('Duration (HH:MM:SS)')
	user_id         = fields.Many2one('res.users','User',ondelete='cascade',required=True)
	state           = fields.Selection(
		selection= [
			('logged_in','Logged In'),
			('logged_out','Logged Out'),
			('timed_out','Timeout'),
			('terminated','Terminated'),
			('error','Login Failed'),
			('unknown', 'Unknown')
		],
		default  = 'logged_in',
		required = True,
		readonly = True,
	)
	country_id = fields.Many2one('res.country', compute=_compute_country_id, store=True)
	last_activity_on = fields.Float('Last Activity On', compute=_compute_last_activity_on)

	_sql_constraints = [('session_id_unique','unique(session_id)','Duplicate session id detected')]

	@api.model
	def save_session(self,uid=False,state=False):
		forwarded_for = request.httprequest.headers.environ.get('HTTP_X_FORWARDED_FOR')
		if forwarded_for:
			ip = forwarded_for.split(',')[0]
		else:
			ip = request.httprequest.headers.environ['REMOTE_ADDR']
		user_agent = request.httprequest.user_agent
		session = request.env['session.session'].sudo().create(
			{
				'user_id'        : uid or request.uid,
				'session_id'     : state != 'error' and request.session.sid,
				'date_login'     : fields.datetime.utcnow(),
				'ip'             : ip,
				'platform'       : user_agent.platform,
				'browser'        : user_agent.browser,
				'browser_version': user_agent.version,
				'user_agent'     : user_agent.string,
				'state'          : state or 'logged_in',
				'active'         : state != 'error' and True,
			}
		)
		try:
			self._cr.commit()
		except Exception:
			self.sudo()._cr.commit()
		return session

	def terminate(self):
		sessions = self.env['session.session']
		for rec in self:
			if rec.active and not rec.is_current:
				session = root.session_store.get(rec.session_id)
				session.logout(keep_db=True)
				root.session_store.delete(session)
			sessions += rec
		sessions._logout('terminated')

	def _logout(self, state):
		sessions = self
		if not sessions:
			sessions = self.sudo().search(
				[
					('session_id','=',request.session.sid),
					('active','=',True),
				]
			)
		sessions.sudo().write(
			{
				'active'     : False,
				'date_logout': fields.datetime.utcnow(),
				'state'      : state,
			}
		)
		self._cr.commit()

	@api.model
	def handle_inactive_sessions(self):
		# Remove Archived Session Records
		days = int(
			self.env['ir.config_parameter'].get_param(
				'odoo_user_login_security.clear_inactive_session_after',
				90,
			)
		)
		days_before = fields.datetime.utcnow() + fields.date_utils.relativedelta(days=-days)
		sessions = self.search(
			[
				('active','=',False),
				('date_logout','<',days_before),
			]
		)
		sessions.unlink()

		# Archive Records for Inactive Sessions
		days = int(
			self.env['ir.config_parameter'].get_param(
				'odoo_user_login_security.end_inactive_session_after',
				7,
			)
		)
		days_before = fields.datetime.utcnow() + fields.date_utils.relativedelta(days=-days)
		sessions = self.search(
			[
				('active','=',True),
				('date_login','<',days_before)
			]
		)
		deadline = time()-days*86400 # 24h*60m*60s = 86400
		for rec in sessions:
			if rec.last_activity_on < deadline:
				session = root.session_store.get(rec.session_id)
				session.logout(keep_db=True)
				rec._logout('timed_out')

	def send_login_email(self, status):
		self.ensure_one()
		if self.user_id.email:
			get_param = self.env['ir.config_parameter'].sudo().get_param
			mail_template = False
			if status == 'suspicious' and get_param('odoo_user_login_security.send_suspicious_login_email'):
				mail_template = self.env.ref('odoo_user_login_security.mail_login_suspicious')
			elif status == 'error' and get_param('odoo_user_login_security.send_failed_login_email'):
				mail_template = self.env.ref('odoo_user_login_security.mail_login_failure')
			if mail_template:
				mail_template.send_mail(self.id, force_send=True)
