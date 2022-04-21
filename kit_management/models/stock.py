# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import fields, models, api
from odoo.tools import float_round
from itertools import groupby
from operator import itemgetter
from odoo.tools.float_utils import float_compare, float_is_zero


class StockMove(models.Model):
    _inherit = 'stock.move'

    kit_line_id = fields.Many2one('product.kit', string='Kit Line')

    def _compute_product_kit_quantities(self, product_id, kit_qty, filters):
        qty_ratios = []
        for kit in product_id.product_kit_ids:
            # print("bom-line", bom_line)
            # print("kit", kit)
            # skip service since we never deliver them
            if kit.component_id.type == 'service':
                continue
            if float_is_zero(kit.qty, precision_rounding=kit.uom_id.rounding):
                # As BoMs allow components with 0 qty, a.k.a. optionnal components, we simply skip those
                # to avoid a division by zero.
                continue
            bom_line_moves = self.filtered(lambda m: m.kit_line_id == kit)
            if bom_line_moves:
                # We compute the quantities needed of each components to make one kit.
                # Then, we collect every relevant moves related to a specific component
                # to know how many are considered delivered.
                uom_qty_per_kit = kit.qty * kit_qty / kit_qty
                qty_per_kit = kit.uom_id._compute_quantity(uom_qty_per_kit, kit.uom_id)
                if not qty_per_kit:
                    continue
                incoming_moves = bom_line_moves.filtered(filters['incoming_moves'])
                outgoing_moves = bom_line_moves.filtered(filters['outgoing_moves'])
                qty_processed = sum(incoming_moves.mapped('product_qty')) - sum(outgoing_moves.mapped('product_qty'))
                # We compute a ratio to know how many kits we can produce with this quantity of that specific component
                qty_ratios.append(
                    float_round(qty_processed / qty_per_kit, precision_rounding=kit.component_id.uom_id.rounding))
            else:
                return 0.0
        if qty_ratios:
            # Now that we have every ratio by components, we keep the lowest one to know how many kits we can produce
            # with the quantities delivered of each component. We use the floor division here because a 'partial kit'
            # doesn't make sense.
            return min(qty_ratios) // 1
        else:
                return 0.0

    @api.model_create_multi
    def create(self, vals_list):
        new_vallist = []
        for line in vals_list:
            if line.get('product_id'):
                product = self.env['product.product'].browse(line.get('product_id'))
                picking = self.env['stock.picking'].browse(line.get('picking_id'))
                picking_type = self.env['stock.picking.type'].browse(line.get('picking_type_id'))
                if picking.picking_type_id.code == 'outgoing' or picking_type.code == 'outgoing':
                    if product.is_kit:
                        if product.product_kit_ids:
                            for component in product.product_kit_ids:
                                if component.component_id.type != 'service':
                                    new_line = line.copy()
                                    new_line.update({'name': component.component_id.name})
                                    new_line['product_id'] = component.component_id.id
                                    new_line['product_uom_qty'] = component.qty * line.get('product_uom_qty')
                                    new_line['kit_line_id'] = component.id
                                    if self.env.context.get('auto_receipt'):
                                        new_line['quantity_done'] = component.qty * line.get('product_uom_qty')
                                    new_vallist.append(new_line)
        for val in vals_list:
            if val.get('product_id'):
                product = self.env['product.product'].browse(val.get('product_id'))
                if not product.is_kit:
                    new_vallist.append(val)
                else:
                    picking = self.env['stock.picking'].browse(val.get('picking_id'))
                    picking_type = self.env['stock.picking.type'].browse(val.get('picking_type_id'))
                    if picking.picking_type_id.code != 'outgoing' and picking_type.code != 'outgoing':
                        new_vallist.append(val)

        res = super(StockMove, self).create(new_vallist)

        return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     res = super(StockMove, self).create(vals_list)
    #     old = res
    #     print(",mmmmm", res, res.product_id.name)
    #     if res.product_id.is_kit and res.product_id.product_kit_ids:
    #         for component in res.product_id.product_kit_ids:
    #             new_move = self.env['stock.move'].create(
    #                 {'product_id': component.component_id.id, 'product_uom': component.component_id.uom_id.id,
    #                  'name': component.component_id.name, 'location_id': res.location_id.id,
    #                  'location_dest_id': res.location_dest_id.id})
    #             new_move.product_id = component.component_id.id
    #             new_move.product_uom_qty = component.qty * res.product_uom_qty
    #             new_move.product_uom = component.component_id.uom_id
    #             if self.env.context.get('auto_receipt'):
    #                 new_move.quantity_done = component.qty * res.product_uom_qty
    #             print("newww", new_move, old)
    #     print("rrr",res)
    #     return res

    def _merge_moves(self, merge_into=False):
        if self.env.context.get('auto_receipt_kit'):
            distinct_fields = self._prepare_merge_moves_distinct_fields()

            candidate_moves_list = []
            if not merge_into:
                for picking in self.mapped('picking_id'):
                    candidate_moves_list.append(picking.move_lines)
            else:
                candidate_moves_list.append(merge_into | self)

            # Move removed after merge
            moves_to_unlink = self.env['stock.move']
            moves_to_merge = []
            for candidate_moves in candidate_moves_list:
                # First step find move to merge.
                candidate_moves = candidate_moves.with_context(prefetch_fields=False)
                for k, g in groupby(sorted(candidate_moves, key=self._prepare_merge_move_sort_method),
                                    key=itemgetter(*distinct_fields)):
                    moves = self.env['stock.move'].concat(*g).filtered(
                        lambda m: m.state not in ('done', 'cancel', 'draft'))

                    # If we have multiple records we will merge then in a single one.
                    # if len(moves) > 1:
                    #     moves_to_merge.append(moves)
            # second step merge its move lines, initial demand, ...
            for moves in moves_to_merge:
                # link all move lines to record 0 (the one we will keep).
                moves.mapped('move_line_ids').write({'move_id': moves[0].id})
                # merge move data
                moves[0].write(moves._merge_moves_fields())
                # update merged moves dicts
                moves_to_unlink |= moves[1:]

            if moves_to_unlink:
                # We are using propagate to False in order to not cancel destination moves merged in moves[0]
                moves_to_unlink._clean_merged()
                moves_to_unlink._action_cancel()
                moves_to_unlink.sudo().unlink()
            return (self | self.env['stock.move'].concat(*moves_to_merge)) - moves_to_unlink
        else:
            return super(StockMove, self)._merge_moves(merge_into=False)
