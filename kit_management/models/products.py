# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_kit = fields.Boolean('Kit', default=False)
    product_kit_ids = fields.One2many('product.kit', 'product_id', string='Product Kit')


class ProductKit(models.Model):
    _name = 'product.kit'
    _description = 'Product Kit'
    _rec_name = 'component_id'

    product_id = fields.Many2one('product.template')
    component_id = fields.Many2one('product.product', string='Component')
    qty = fields.Float('Quantity')
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    cost = fields.Float(related='component_id.standard_price', string='Unit Cost')

    @api.onchange('component_id')
    def onchange_component_id(self):
        self.uom_id = self.component_id.uom_id
