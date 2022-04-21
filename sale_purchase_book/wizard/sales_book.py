# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models
import datetime
import calendar
import base64


class SaleBookWizard(models.TransientModel):
    _name = 'sale.book.wizard'
    _description = 'Adding filters for reports'

    filter_type = fields.Selection([('by_date', 'By Date Period'), ('by_month', 'By Month')],
                            string='Filter Type', default='by_month')
    month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'),
                              ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'), ('10', 'October'),
                              ('11', 'November'), ('12', 'December')], string='Month', default=str(datetime.datetime.today().month))
    from_date = fields.Date(string='Start Date')
    to_date = fields.Date(string='To Date')
    sale_book_file = fields.Binary('Sale book Report')
    file_name = fields.Char('File Name')
    report_printed = fields.Boolean('Report Printed')

    @api.onchange('month')
    def onchange_month(self):
        self.from_date = datetime.datetime.today().replace(month=int(self.month), day=1)
        self.to_date = self.from_date + datetime.timedelta(calendar.monthrange(datetime.datetime.today().year, int(self.month))[1]-1)

    def print_xls_report(self):
        new_file = self.env['purchase.sale.book'].excel_report_generate('sale', self.from_date, self.to_date)
        output = base64.encodebytes(new_file)
        self.sale_book_file = output
        self.file_name = 'Sale Book.xlsx'
        self.report_printed = True
        return {
            'view_mode': 'form',
            'res_id': self.id,
            'res_model': 'sale.book.wizard',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'target': 'new',
        }




