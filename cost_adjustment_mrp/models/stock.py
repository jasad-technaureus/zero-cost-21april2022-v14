# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet
from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_repr

from datetime import date, datetime
from collections import defaultdict
from odoo.exceptions import UserError


class ProcurementException(Exception):
    """An exception raised by ProcurementGroup `run` containing all the faulty
    procurements.
    """

    def __init__(self, procurement_exceptions):
        """:param procurement_exceptions: a list of tuples containing the faulty
        procurement and their error messages
        :type procurement_exceptions: list
        """
        self.procurement_exceptions = procurement_exceptions


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(StockValuationLayer, self).create(vals_list)
        for layer in res:
            if layer.product_id.is_kit_product:
                svl_with_same_picking = self.env['stock.valuation.layer'].search(
                    [('transfer_id', '=', layer.transfer_id.id)])
                print('product...', layer.product_id.name, svl_with_same_picking.mapped('product_id').ids)
                print('svl_with_same_picking', svl_with_same_picking)
                bom_products = []

                for bom in layer.product_id.bom_ids:
                    if bom.bom_line_ids:
                        bom_products += bom.bom_line_ids.mapped('product_id').ids
                print('bom_products', bom_products, layer.product_id.bom_ids)
                component_svl = svl_with_same_picking.filtered(lambda x: x.product_id.id in bom_products)
                print('component_svl', component_svl)
                total_value = sum(component_svl.mapped('value'))
                total_qty = sum(component_svl.mapped('value'))
                layer.value = total_value
                layer.unit_cost = total_value / layer.quantity
                print('total_value...', total_value)

            if layer.stock_move_id.production_id or layer.stock_move_id.raw_material_production_id:
                layer.operation_type = 'mrp_operation'
                layer.blank_type = False
                if layer.stock_move_id.production_id:
                    layer.location_name = layer.stock_move_id.production_id.location_dest_id.complete_name
                elif layer.stock_move_id.raw_material_production_id:
                    layer.location_name = layer.stock_move_id.raw_material_production_id.location_src_id.complete_name
                    print('---->', layer.location_name)
                if not layer.stock_move_id.real_date:
                    layer.stock_move_id.real_date = layer.stock_move_id.production_id.real_date if layer.stock_move_id.production_id else layer.stock_move_id.raw_material_production_id.real_date
                    layer.stock_move_id.date = layer.stock_move_id.production_id.real_date if layer.stock_move_id.production_id else layer.stock_move_id.raw_material_production_id.real_date
                # layer.transfer_id=layer.stock_move_id.production_id.id
                layer.real_date = layer.stock_move_id.real_date if layer.stock_move_id.production_id else layer.stock_move_id.raw_material_production_id.real_date
                layer.stock_move_id.date = layer.stock_move_id.real_date if layer.stock_move_id.production_id else layer.stock_move_id.raw_material_production_id.real_date
                print('re..........', layer.real_date)

            if layer.stock_landed_cost_id:
                mrp_layers = self.env['stock.valuation.layer'].search([('operation_type', '=', 'mrp_operation')])
                print('mrp_layers', mrp_layers)
                for svl in mrp_layers:
                    print('SVL', svl, )
                    # mrp_layer = svl.product_id.bom_line_ids.filtered(lambda x: x.product_id == layer.product_id)
                    # print('mrp_layer',mrp_layer)
                    component = svl.stock_move_id.production_id.move_raw_ids.filtered(
                        lambda x: x.product_id == layer.stock_move_id.product_id)
                    print('ccccc', component, component.product_id.name, component.quantity_done)
                    landed_move = layer.stock_landed_cost_id.valuation_adjustment_lines.filtered(
                        lambda x: x.move_id == layer.stock_move_id)
                    landed_cost_unit_cost = landed_move.additional_landed_cost / landed_move.quantity
                    value_to_add = landed_cost_unit_cost * component.quantity_done
                    print('value_to_add', value_to_add)
                    print('Landed', landed_move, landed_move.additional_landed_cost)
                    svl.value += value_to_add
                    svl.unit_cost = svl.value / svl.quantity if svl.quantity else 0.0
                    svl.account_move_id.button_draft()
                    credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
                    debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
                    print('LINE', credit_line.credit, debit_line.debit)
                    svl.account_move_id.action_post()
        return res


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    real_date = fields.Datetime(string='Real Date')
    real_date_display = fields.Datetime(string='Real Date')

    def _compute_show_valuation(self):
        for order in self:
            order.show_valuation = any(m.state == 'done' for m in order.move_finished_ids)
            if order.state == 'cancel':
                order.show_valuation = True

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        if not self.real_date_display:
            self.real_date = datetime.now()
            self.real_date_display = datetime.now()
        return res

    @api.onchange('real_date', 'real_date_display')
    def onchange_real_date(self):
        print('real_date.............', self.real_date, self.real_date_display)
        if self.real_date_display:
            self.real_date = self.real_date_display
            import pytz
            local = pytz.timezone(self.env.user.tz)
            print('local...', local)
            display_date_result = datetime.strftime(
                pytz.utc.localize(datetime.strptime(str(self.real_date), "%Y-%m-%d %H:%M:%S")).astimezone(
                    local), "%Y-%m-%d %H:%M:%S")
            print('display_date_result', display_date_result, type(display_date_result))
            self.real_date = datetime.strptime(display_date_result, "%Y-%m-%d %H:%M:%S")
        if self.real_date and self.real_date > datetime.now():
            raise UserError(_('Choose a Date less than or equal to Today'))
        if self.state == 'done':
            journals = ''
            if self.move_raw_ids:
                for move in self.move_raw_ids:
                    if move.account_move_ids:
                        for journal in move.account_move_ids:
                            journals += journal.name + '\n'
            return {
                'warning': {'title': "Warning",
                            'message': "You are changing the Real Date of this inventory transfer. Do not forget to change the accounting date of the following journal entries.\n%s" % journals}
            }

    def action_cancel(self):
        res = super(MrpProduction, self).action_cancel()
        for production in self:
            if production.state == 'done':
                context = self.env.context.copy()
                context.update({'cancel_picking': True})
                self.env.context = context
                production.move_raw_ids._action_cancel()
                production.move_finished_ids._action_cancel()
        return res


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    @api.onchange('type')
    def _onchange_kit_type(self):
        if self.type == 'phantom' and self.product_tmpl_id.type == 'consu':
            self.product_tmpl_id.is_kit_product = True
        else:
            self.product_tmpl_id.is_kit_product = False
        print('type....', self.product_tmpl_id.name, self.product_tmpl_id.is_kit_product)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_kit_product = fields.Boolean(string='Is Kit Product')


# class ProductProduct(models.Model):
#     _inherit = 'product.product'
#
#     is_kit_product = fields.Boolean(string='Is Kit Product', related='product_tmpl_id.is_kit_product', store=True)


class StockMove(models.Model):
    _inherit = 'stock.move'

    def create(self, vals_list):
        res = super(StockMove, self).create(vals_list)
        for move in res:
            if move.production_id or move.raw_material_production_id:
                print('res--->', move.product_id.name)
                move.real_date = move.production_id.real_date if move.production_id else move.raw_material_production_id.real_date
                print('RRRRRR', move.real_date)

        return res

    def action_explode(self):
        print('move---->', self)
        """ Explodes pickings """
        # in order to explode a move, we must have a picking_type_id on that move because otherwise the move
        # won't be assigned to a picking and it would be weird to explode a move into several if they aren't
        # all grouped in the same picking.
        moves_ids_to_return = OrderedSet()
        moves_ids_to_unlink = OrderedSet()
        phantom_moves_vals_list = []
        for move in self:
            if not move.picking_type_id or (move.production_id and move.production_id.product_id == move.product_id):
                moves_ids_to_return.add(move.id)
                continue
            bom = self.env['mrp.bom'].sudo()._bom_find(product=move.product_id, company_id=move.company_id.id,
                                                       bom_type='phantom')
            if not bom or move.product_id.is_kit_product:
                moves_ids_to_return.add(move.id)
                continue
            if move.picking_id.immediate_transfer:
                factor = move.product_uom._compute_quantity(move.quantity_done, bom.product_uom_id) / bom.product_qty
            else:
                factor = move.product_uom._compute_quantity(move.product_uom_qty, bom.product_uom_id) / bom.product_qty
            boms, lines = bom.sudo().explode(move.product_id, factor, picking_type=bom.picking_type_id)
            for bom_line, line_data in lines:
                if move.picking_id.immediate_transfer:
                    phantom_moves_vals_list += move._generate_move_phantom(bom_line, 0, line_data['qty'])
                else:
                    phantom_moves_vals_list += move._generate_move_phantom(bom_line, line_data['qty'], 0)
            # delete the move with original product which is not relevant anymore
            moves_ids_to_unlink.add(move.id)
        self.env['stock.move'].browse(moves_ids_to_unlink).sudo().unlink()

        if phantom_moves_vals_list:
            print('phantom_moves_vals_list', phantom_moves_vals_list)
            phantom_moves = self.env['stock.move'].create(phantom_moves_vals_list)
            phantom_moves._adjust_procure_method()
            moves_ids_to_return |= phantom_moves.action_explode().ids
        print('moves_ids_to_return', moves_ids_to_return)
        return self.env['stock.move'].browse(moves_ids_to_return)


class StockRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'stock.rule'

    @api.model
    def _run_pull(self, procurements):
        moves_values_by_company = defaultdict(list)
        mtso_products_by_locations = defaultdict(list)

        # To handle the `mts_else_mto` procure method, we do a preliminary loop to
        # isolate the products we would need to read the forecasted quantity,
        # in order to to batch the read. We also make a sanitary check on the
        # `location_src_id` field.
        for procurement, rule in procurements:
            if not rule.location_src_id:
                msg = _('No source location defined on stock rule: %s!') % (rule.name,)
                raise ProcurementException([(procurement, msg)])

            if rule.procure_method == 'mts_else_mto':
                mtso_products_by_locations[rule.location_src_id].append(procurement.product_id.id)

        # Get the forecasted quantity for the `mts_else_mto` procurement.
        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            products = self.env['product.product'].browse(product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {product.id: product.free_qty for product in products}

        # Prepare the move values, adapt the `procure_method` if needed.
        for procurement, rule in procurements:
            procure_method = rule.procure_method
            if rule.procure_method == 'mts_else_mto':
                qty_needed = procurement.product_uom._compute_quantity(procurement.product_qty,
                                                                       procurement.product_id.uom_id)
                qty_available = forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id]
                if float_compare(qty_needed, qty_available,
                                 precision_rounding=procurement.product_id.uom_id.rounding) <= 0:
                    procure_method = 'make_to_stock'
                    forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                else:
                    procure_method = 'make_to_order'

            move_values = rule._get_stock_move_values(*procurement)
            move_values['procure_method'] = procure_method
            moves_values_by_company[procurement.company_id.id].append(move_values)

        for company_id, moves_values in moves_values_by_company.items():
            new_move = moves_values[0].copy()
            print('moves_values', moves_values)
            sale_line = moves_values[0].get('sale_line_id')
            sale_order_line = self.env['sale.order.line'].browse(sale_line)
            if sale_order_line.product_id.is_kit_product:
                new_move['product_id'] = sale_order_line.product_id.id
                new_move['product_uom_qty'] = sale_order_line.product_uom_qty
                moves_values.append(new_move)
            print('moves_values', moves_values)
            # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            moves = self.env['stock.move'].with_user(SUPERUSER_ID).sudo().with_company(company_id).create(moves_values)
            # print('moves...........1', moves[2], moves[2].product_id.name)

            # Since action_confirm launch following procurement_group we should activate it.
            moves._action_confirm()
        return True
