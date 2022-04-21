# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_price_unit(self):
        """Get correct price with discount replacing current price_unit
        value before calling super and restoring it later for assuring
        maximum inheritability.
        """
        price_unit = False
        po_line = self.purchase_line_id
        if po_line and self.product_id == po_line.product_id:
            price = po_line._get_discounted_price_unit()
            if price != po_line.price_unit:
                price_unit = po_line.price_unit
                po_line.price_unit = price
        res = super()._get_price_unit()
        if price_unit:
            po_line.price_unit = price_unit
        return res
