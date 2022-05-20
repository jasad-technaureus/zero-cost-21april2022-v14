# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.


from odoo import fields, models, api

from itertools import groupby
from collections import defaultdict


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        self.ensure_one()
        lines_by_product = groupby(sorted(lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
        print('lines_by_product', lines_by_product)
        move_vals = []
        lines_data = defaultdict(dict)
        for product_id, olines in lines_by_product:
            order_lines = self.env['pos.order.line'].concat(*olines)
            print('order_lines....', order_lines)
            move_vals.append(self._prepare_stock_move_vals(order_lines[0], order_lines))
            lines_data[product_id].update({'order_lines': order_lines})
            print('move_vals......', move_vals)
        for move in move_vals:
            product_id = self.env['product.product'].browse(move.get('product_id'))
            if product_id and product_id.is_kit_product:
                bom = self.env['mrp.bom'].sudo()._bom_find(product=product_id, company_id=self.company_id.id,
                                                           bom_type='phantom')
                if bom:
                    bom_lines = bom.bom_line_ids.mapped('product_id')
                    for product in bom_lines:
                        new_move = move.copy()
                        new_move['product_id'] = product.id
                        print('new_move....', new_move)
                        move_vals.append(new_move)
        print('move_vals', move_vals)
        moves = self.env['stock.move'].create(move_vals)
        print('moves....',moves)
        for move in moves:
            lines_data[move.product_id.id].update({'move': move})
        confirmed_moves = moves._action_confirm()
        # Confirmed moves with product_id not in lines. This can happen e.g. when product_id has a phantom-type bom.
        confirmed_moves_to_assign = confirmed_moves.filtered(
            lambda m: m.product_id.id not in lines_data or m.product_id.tracking == 'none')
        self._create_move_lines_for_pos_order(confirmed_moves_to_assign, set_quantity_done_on_move=True)
        confirmed_moves_remaining = confirmed_moves - confirmed_moves_to_assign
        if self.picking_type_id.use_existing_lots or self.picking_type_id.use_create_lots:
            existing_lots = self._create_production_lots_for_pos_order(lines)
            move_lines_to_create = []
            for move in confirmed_moves_remaining:
                if lines_data[move.product_id.id].get('order_lines'):
                    for line in lines_data[move.product_id.id]['order_lines']:
                        sum_of_lots = 0
                        for lot in line.pack_lot_ids.filtered(lambda l: l.lot_name):
                            if line.product_id.tracking == 'serial':
                                qty = 1
                            else:
                                qty = abs(line.qty)
                            ml_vals = dict(move._prepare_move_line_vals(), qty_done=qty)
                            if existing_lots:
                                existing_lot = existing_lots.filtered_domain(
                                    [('product_id', '=', line.product_id.id), ('name', '=', lot.lot_name)])
                                quant = self.env['stock.quant']
                                if existing_lot:
                                    quant = self.env['stock.quant'].search(
                                        [('lot_id', '=', existing_lot.id), ('quantity', '>', '0.0'),
                                         ('location_id', 'child_of', move.location_id.id)],
                                        order='id desc',
                                        limit=1
                                    )
                                ml_vals.update({
                                    'lot_id': existing_lot.id,
                                    'location_id': quant.location_id.id or move.location_id.id
                                })
                            else:
                                ml_vals.update({'lot_name': lot.lot_name})
                            move_lines_to_create.append(ml_vals)
                            sum_of_lots += qty
                        if abs(line.qty) != sum_of_lots:
                            difference_qty = abs(line.qty) - sum_of_lots
                            ml_vals = lines_data[move.product_id.id]['move']._prepare_move_line_vals()
                            if line.product_id.tracking == 'serial':
                                ml_vals.update({'qty_done': 1})
                                move_lines_to_create.extend([ml_vals for i in range(int(difference_qty))])
                            else:
                                ml_vals.update({'qty_done': difference_qty})
                                move_lines_to_create.append(ml_vals)

            self.env['stock.move.line'].create(move_lines_to_create)
        else:
            self._create_move_lines_for_pos_order(confirmed_moves_remaining)
