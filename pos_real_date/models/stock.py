# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.


from odoo import fields, models, api
from odoo.http import request


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
        res = super(StockPicking, self)._create_picking_from_pos_order_lines(location_dest_id, lines, picking_type,
                                                                             partner=False)
        for rec in res:
            if rec.date_done:
                rec.update({'real_date': rec.date_done})
        return res


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'
    pos_order_id = fields.Many2one('pos.order', string='POS Order')

    def _compute_move_type(self):
        res = super(StockValuationLayer, self)._compute_move_type()
        print('lllll.........',self)
        for val in self:
            val.qty_sold = abs(val.quantity)
            print('val.stock_move_id',val.stock_move_id,val.stock_move_id.picking_id.pos_session_id)
            print('val.stock_move_id',val.stock_move_id,val.stock_move_id.picking_id)
            if val.stock_move_id.picking_id.pos_session_id:
                pos_order = self.env['pos.order'].search(
                    [('session_id', '=', val.stock_move_id.picking_id.pos_session_id.id)])
                print('pos_order', pos_order)
                val.pos_order_id = pos_order.id
                order_line = pos_order.lines.filtered(lambda x: x.product_id == val.product_id)
                val.invoiced_unit_price = order_line.price_unit
                val.invoiced_amount = val.invoiced_unit_price * abs(val.quantity)
        return res
