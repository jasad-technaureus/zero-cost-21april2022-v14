# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import fields,http
from odoo.http import request


browser_logo_files = {
	'chrome' : 'chrome.png',
	'edge'   : 'edge.png',
	'firefox': 'firefox.png',
	'msie'   : 'msie.png',
	'opera'  : 'opera.png',
	'safari' : 'safari.png',
}
platform_logo_files = {
	'android' : 'android.png',
	'chromeos': 'chromeOS.png',
	'ipad'    : 'ipad.png',
	'iphone'  : 'iphone.png',
	'linux'   : 'linux.png',
	'macos'   : 'macos.png',
	'windows' : 'windows.png',
	'other'   : 'browser.png',
}
logo_file ='/odoo_user_login_security/static/src/img/'


class WebsiteBackend(http.Controller):
	@http.route('/session/fetch_dashboard_data',type="json",auth='user')
	def fetch_dashboard_data(self,tz,**kw):
		browser_selections  = dict(request.env['session.session']._fields.get('browser').selection)
		platform_selections = dict(request.env['session.session']._fields.get('platform').selection)

		recent_sessions = request.env['session.session'].search_read(
			domain = [],
			fields = ['id','browser','date_login','ip','platform','user_id'],
			limit  = 5,
			order  = 'date_login desc',
		)
		for session in recent_sessions:
			browser  = session.get('browser')
			platform = session.get('platform')

			date_login = fields.Datetime.context_timestamp(
				request.env.user.with_context(tz=tz),
				session.get('date_login'),
			).replace(tzinfo=None)

			browser_logo_file = logo_file + browser_logo_files.get(browser,'browser.png')
			platform_logo_file = logo_file + platform_logo_files.get(platform,'browser.png')

			session.update(
				date_login    = date_login,
				user          = session.pop('user_id')[1],
				platform_name = platform_selections.get(platform),
				browser_name  = browser_selections.get(browser),
				browser_logo  = browser_logo_file,
				platform_logo = platform_logo_file,
			)

		browser_sessions = []
		sessions = request.env['session.session'].search(
			[
				'|',
				('active','=',True),
				('active','=',False),
			]
		)
		for browser,label in browser_selections.items():
			all_sessions = sessions.filtered(lambda self: self.browser == browser)
			active_sessions = all_sessions.filtered(lambda self: self.active == True)
			browser_logo_file = logo_file + browser_logo_files.get(browser,'browser.png')
			platform_logo_file = logo_file + platform_logo_files.get(browser,'browser.png')
			browser_sessions.append(
				{
					'browser'      : browser,
					'browser_name' : label,
					'total_count'  : len(all_sessions),
					'active_count' : len(active_sessions),
					'browser_logo' : browser_logo_file,
					'platform_logo': platform_logo_file,
				}
			)
		browser_sessions = sorted(
			browser_sessions,
			key=lambda k:(k['browser']=='other',k['browser'])
		)

		state_counts = []
		for state,label in sessions._fields.get('state').selection:
			state_counts.append(
				{
					'state' : state,
					'status': label,
					'count' : len(sessions.filtered(lambda self:self.state == state)),
				}
			)

		return {
			'browser_sessions': browser_sessions,
			'recent_sessions' : recent_sessions,
			'state_counts'    : state_counts,
		}
