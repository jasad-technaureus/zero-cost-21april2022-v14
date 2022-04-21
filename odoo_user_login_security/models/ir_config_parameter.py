# -*- coding: utf-8 -*-
##############################################################################
# Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# See LICENSE file for full copyright and licensing details.
# License URL : <https://store.webkul.com/license.html/>
##############################################################################
from odoo import api,models,tools


class IrConfigParameter(models.Model):
	_inherit = 'ir.config_parameter'

	@api.model
	@tools.ormcache('self.env.cr.dbname')
	def _get_delay(self):
		return int(
			self.env['ir.config_parameter'].sudo().get_param(
				'odoo_user_login_security.inactive_session_time_out_delay',0,
			)
		)

	@api.model
	@tools.ormcache('self.env.cr.dbname')
	def _get_urls(self):
		return self.env['ir.config_parameter'].sudo().get_param(
			'odoo_user_login_security.inactive_session_time_out_ignored_url','',
		).split(',')

	def write(self, vals):
		res = super(IrConfigParameter, self).write(vals)
		self._get_delay.clear_cache(
			self.filtered(
				lambda r: r.key == 'odoo_user_login_security.inactive_session_time_out_delay'
			),
		)
		self._get_urls.clear_cache(
			self.filtered(
				lambda r: r.key == 'odoo_user_login_security.inactive_session_time_out_ignored_url'
			),
		)
		return res
