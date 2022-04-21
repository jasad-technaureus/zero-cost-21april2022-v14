# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _


class AccountTax(models.Model):
    _inherit = 'account.tax'

    exempt_vat = fields.Selection([('type_1', 'TYPE 1'),
                                    ('type_2', 'TYPE 2'),
                                    ('tax_free', 'TAX FREE'),
                                    ('margin_scheme', 'MARGIN SCHEME'),
                                    ('export_of_goods', 'EXPORT OF GOODS')], string='Exempt from VAT')


    code_ubl = fields.Selection([('vatex-eu-132-1a', 'Perjashtim i llojit 1'),
                                 ('vatex-eu-132-1b', 'Perjashtim i llojit 2'),
                                 ('vatex-eu-o', 'Pa TVSH'),
                                 ('vatex-eu-d', 'Marzhi i shitjes-agjent udhetimi'),
                                 ('vatex-eu-f', 'Marzhi i shitjes-mallra te perdorura'),
                                 ('vatex-eu-i', 'Marzhi i shitjes-vepra arti'),
                                 ('vatex-eu-g', 'Eksport')], 'Kodi i perjashtimit per UBL')
    arsye_perjashtimi = fields.Char('Arsyeja e perjashtimit nga TVSH', size=256)