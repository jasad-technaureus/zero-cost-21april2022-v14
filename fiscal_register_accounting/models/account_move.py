# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields, _
from ast import literal_eval
import base64
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    fiscal_device_id = fields.Many2one('fiscal.devices', string='Fiscal Printer',
                                       default=lambda self: self._get_default_access_token())
    is_fiscal_print = fields.Boolean(string='Print in Fiscal Device', copy=False, default=False)
    cust_request = fields.Boolean(string="Requested By Customer", default=False)
    summary_file = fields.Binary('Report')

    def _get_default_access_token(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        default_fiscal_printer = literal_eval(
            ICPSudo.get_param('fiscal_register_accounting.def_fiscal_device_id',
                              default='False'))
        return default_fiscal_printer

    def action_post(self):
        super(AccountMove, self).action_post()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        max_amt = literal_eval(
            ICPSudo.get_param('fiscal_register_accounting.max_amount_move',
                              default='False'))
        if max_amt:
            if not self.fiscal_device_id.file_name and self.is_fiscal_print:
                raise UserError(_("Please add file name in the Fiscal Device."))
            amt_total = self.amount_total
            if self.company_currency_id != self.currency_id:
                amt_total = self.currency_id._convert(self.amount_total, self.company_currency_id, self.company_id,
                                                      fields.Date.context_today(self))

            if amt_total < max_amt:
                if self.fiscal_device_id and self.is_fiscal_print:
                    lines = ''
                    if self.fiscal_device_id.header:
                        header = self.fiscal_device_id.header.split("\n")
                        for head in header:
                            # head =
                            lines += (head + "\r\n")
                        lines += "\r\n"
                        # lines += "\r\n"
                    if self.cust_request:
                        lines += 'inp num=%s, TERM=TSFATS' % self.name
                        lines += "\r\n"
                        lines += "\r\n"
                    if self.invoice_line_ids:
                        for line in self.invoice_line_ids:
                            if self.fiscal_device_id.prd_dynamic:
                                price_unit = line.price_unit
                                REP = 0
                                if line.tax_ids:
                                    tax = line.tax_ids[0].id
                                    if tax == self.fiscal_device_id.vat1.id:
                                        REP = 1
                                    elif tax == self.fiscal_device_id.vat2.id:
                                        REP = 2
                                    elif tax == self.fiscal_device_id.vat3.id:
                                        REP = 3
                                    elif tax == self.fiscal_device_id.vat4.id:
                                        REP = 4
                                    elif tax == self.fiscal_device_id.vat5.id:
                                        REP = 5
                                    if line.tax_ids[0].price_include:
                                        price_unit = line.price_unit
                                    else:
                                        price_unit = (line.price_unit * (
                                            line.tax_ids[0].amount) / 100) + line.price_unit

                                lines += self.fiscal_device_id.prd_dynamic % (
                                REP, line.quantity, price_unit, line.name[0:20])
                                lines += "\r\n"
                                if line.discount:
                                    lines += 'PERCA ALIQ=' + str(line.discount)
                                    lines += "\r\n"
                        lines += "\r\n"
                    if self.fiscal_device_id.footer_inv:
                        footer = self.fiscal_device_id.footer_inv.split("\n")
                        for foot in footer:
                            lines += (foot + "\r\n")
                        # lines += self.fiscal_device_id.footer_inv
                        # lines += "\r\n"
                    new_file = base64.encodebytes(bytes(lines, 'utf-8'))
                    self.summary_file = new_file
                    # values = {
                    #     'name': self.name+".txt",
                    #     'store_fname': self.name+".txt",
                    #     'res_model': 'account.move',
                    #     'res_id': False,
                    #     'type': 'binary',
                    #     'public': True,
                    #     'datas': new_file,
                    # }
                    # attachment_id = self.env['ir.attachment'].sudo().create(values)
                    # download_url = '/web/content/' + str(attachment_id.id) + '?download=True'
                    # base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    #
                    # return {
                    #     "type": "ir.actions.act_url",
                    #     "url": str(base_url) + str(download_url),
                    #     "target": "new",
                    # }

                    return {
                        'type': 'ir.actions.act_url',
                        'url': 'web/content/?model=account.move&'
                               'field=summary_file&download=true&id=%s&filename=%s.txt' % (
                               self.id, self.fiscal_device_id.file_name),
                        'target': 'new',
                    }
