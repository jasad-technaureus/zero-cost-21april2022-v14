# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class DeviceTypes(models.Model):
    _name = 'device.type'
    _description = 'Defining device types'

    name = fields.Char(string='Device Type')


class FiscalDevices(models.Model):
    _name = 'fiscal.devices'
    _description = 'Configuring device and its template'

    name = fields.Char(string='Device Name')
    type = fields.Many2one('device.type')
    vat1 = fields.Many2one('account.tax', string='VAT 1')
    vat2 = fields.Many2one('account.tax', string='VAT 2')
    vat3 = fields.Many2one('account.tax', string='VAT 3')
    vat4 = fields.Many2one('account.tax', string='VAT 4')
    vat5 = fields.Many2one('account.tax', string='VAT 5')
    header = fields.Text(string="Header Template")
    footer = fields.Text(string='Footer Template')
    footer_inv = fields.Text(string='Invoice Footer')
    prd_dynamic = fields.Text(string='Product Template')
    file_name = fields.Char(string="File Name")
