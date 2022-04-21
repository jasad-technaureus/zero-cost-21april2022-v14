# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    id_type = fields.Selection([('nuis', 'NUIS'),
                                ('id', 'ID'),
                                ('pass', 'PASS '),
                                ('vat', 'VAT'),
                                ('tax', 'TAX'),
                                ('soc', 'SOC')], string='ID Type')
