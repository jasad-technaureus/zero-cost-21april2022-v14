# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def generate_ean13_new(self):
        ean13 = self.product_tmpl_id.generate_ean13(self.browse(self.id))
        self.barcode = ean13
