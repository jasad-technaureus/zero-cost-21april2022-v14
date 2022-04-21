# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _


class PaymentMethods(models.Model):
    _name = 'payment.methods'
    _description = 'Payment Methods'
    _rec_name = 'type'

    code = fields.Char(string='Code')
    description = fields.Char(string='Description')
    type = fields.Selection([('banknote', 'BANKNOTE'),
                             ('card', 'CARD'),
                             ('check', 'CHECK'),
                             ('svoucher', 'SVOUCHER'),
                             ('company', 'COMPANY'),
                             ('oder', 'ORDER'),
                             ('account', 'ACCOUNT'),
                             ('factoring', 'FACTORING'),
                             ('compensation', 'COMPENSATION'),
                             ('transfer', 'TRANSFER'),
                             ('waiver', 'WAIVER'),
                             ('kind', 'KIND'),
                             ('other', 'OTHER')], string='Payment Type')


