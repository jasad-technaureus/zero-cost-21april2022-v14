# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import models, fields
from odoo.tools.misc import format_datetime


class StockValuationLayerRevaluation(models.TransientModel):
    _inherit = 'stock.valuation.layer.revaluation'

    date = fields.Date("Accounting Date", required=True, default=fields.Date.context_today)
