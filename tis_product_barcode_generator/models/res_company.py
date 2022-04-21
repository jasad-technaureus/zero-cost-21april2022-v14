# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    ean_sequence_id = fields.Many2one('ir.sequence', string='Ean sequence')
