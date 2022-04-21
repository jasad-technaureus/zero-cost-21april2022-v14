# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    barcode_sequence = fields.Boolean(string='Barcode Sequence', default=False)
