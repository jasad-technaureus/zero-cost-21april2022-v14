# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import models, fields, _

from odoo.exceptions import UserError


class CostAdjustments(models.Model):
    _name = 'cost.adjustments'
    _description = 'Cost Adjustment'

    product_id = fields.Many2one('product.product', string='Product')
    from_date = fields.Date(string='Date From', compute='_compute_count')
    count = fields.Integer(string='Count', compute='_compute_count')
    active = fields.Boolean(string='Active', default=True)
    is_from_bll = fields.Boolean(string='is from bill', default=False)

    def _compute_count(self):
        product_list = []

        for val in self:
            if val.product_id not in product_list:
                product_list.append(val.product_id)
            else:
                val.unlink()
            valuation_layers_all = self.env['stock.valuation.layer'].search(
                [('product_id', '=', val.product_id.id), ('real_date', '!=', False), ('move_type', '!=', 'in_invoice'),
                 ('state', '=', 'confirm')])
            valuation_layers = valuation_layers_all.filtered(
                lambda
                    x: x.product_id == val.product_id and x.real_date < x.create_date and x.blank_type != 'Adjustment' and x.blank_type != 'Revaluation')
            print('valuation_layers', valuation_layers)
            valuation_layers_all._compute_move_type()
            first_layers = valuation_layers.sorted(key=lambda x: x.real_date)
            if valuation_layers and first_layers and first_layers[0].cost_adjustment_id != val:
                first_layer = first_layers.filtered(lambda x: x.cost_adjustment_id == val)
                if not first_layer:
                    # This means this is the case of different unit price
                    valuation_layers = False

            else:
                if not valuation_layers:
                    valuation_layers = False
                else:
                    first_layer = first_layers[0]

            count = 0
            wrong_in_layer = valuation_layers_all.filtered(
                lambda
                    x: x.product_id == val.product_id and x.real_date < x.create_date and x.blank_type != 'Adjustment' and x.blank_type != 'Revaluation' and x.value > 0)
            if valuation_layers:
                val.from_date = first_layer.real_date
                print('val.from_date', val.from_date, first_layer)
                stock_out_after_real = valuation_layers_all.filtered(
                    lambda
                        x: x.real_date >= first_layer.real_date and (
                            x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.blank_type != 'Adjustment' and x.move_type != 'in_invoice' and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                inv_layer = stock_out_after_real.filtered(
                    lambda x: x.stock_move_id.inventory_id and x.value > 0).sorted(key=lambda x: x.real_date)
                if inv_layer:
                    in_layers = valuation_layers_all.filtered(
                        lambda
                            x: x.real_date < inv_layer[0].real_date and x.value > 0)
                    if not in_layers:
                        stock_out_after_real = stock_out_after_real - inv_layer[0]

                count += len(stock_out_after_real)
                print('count--', count)
                purchase_layers = self.env['stock.valuation.layer'].search(
                    [('product_id', '=', val.product_id.id),
                     ('order_type', '=', 'purchase'), ('margin', '!=', 0)])
                if purchase_layers:
                    count += len(purchase_layers)

                val.count = count
                print('----count', count, len(wrong_in_layer))
                print(count)
            else:
                purchase_layers = self.env['stock.valuation.layer'].search(
                    [('product_id', '=', val.product_id.id),
                     ('order_type', '=', 'purchase'), ('margin', '!=', 0)])
                first_layers = purchase_layers.sorted(key=lambda x: x.real_date)
                if first_layers:
                    val.from_date = first_layers[0].real_date
                    val.count += len(purchase_layers)
                else:
                    val.from_date = False
                    val.count = 0

            if val.count == 0:
                valuation_layers = valuation_layers_all.filtered(
                    lambda
                        x: x.product_id == val.product_id and x.real_date < x.create_date and x.blank_type != 'Adjustment' and x.blank_type != 'Revaluation')
                first_layers = valuation_layers.sorted(key=lambda x: x.real_date)
                if first_layers:
                    first_layer = first_layers[0]
                    stock_out_after_real = valuation_layers_all.filtered(
                        lambda
                            x: x.real_date >= first_layer.real_date and (
                                x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.blank_type != 'Adjustment' and x.move_type != 'in_invoice' and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                    count += len(stock_out_after_real)
                    val.count += count
            if val.count == 0:
                val.from_date = False
                val.active = False

    def cost_adjustment(self):
        view = self.env.ref('cost_adjustments.adjust_cost_warning_wizard')
        return {
            'name': _('Cost Adjustment?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cost.adjust.warning',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

        }

    def ca_adjust_confirm_scheduler(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        automatic_cost_adjustment = ICPSudo.get_param('cost_adjustment.automatic_cost_adjustment')
        if automatic_cost_adjustment:
            print("ca_adjust_confirm_scheduler")
            cost_adjustments = self.env['cost.adjustments'].search([])
            print("cost_adjustments", cost_adjustments)

            for cost_adjustment in cost_adjustments:
                user_error_case = False
                valuation_layers_all = self.env['stock.valuation.layer'].search(
                    [('product_id', '=', cost_adjustment.product_id.id), ('state', '=', 'confirm')])
                print('valuation_layers_all', valuation_layers_all)
                valuation_layer_to_be_sorted = valuation_layers_all.filtered(
                    lambda
                        x: x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                valuation_layers_all._compute_move_type()  # to_calculate_margin

                valuation_layers = valuation_layers_all.filtered(
                    lambda
                        x: x.product_id == cost_adjustment.product_id and x.real_date < x.create_date and x.blank_type != 'Adjustment' and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                print('LLLLLLLLL', valuation_layers)
                return_layer = valuation_layers_all.filtered(lambda x: x.stock_move_id.origin_returned_move_id)
                out_layers = self.env['stock.valuation.layer']
                new_layers = self.env['stock.valuation.layer']
                if valuation_layers:
                    first_layer = valuation_layers.sorted(key=lambda x: x.real_date)
                    out_layers = valuation_layers_all.filtered(
                        lambda x: (
                                          x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                                  first_layer[0].real_date).sorted(
                        key=lambda x: x.real_date)
                    real_dates = valuation_layer_to_be_sorted.mapped('real_date')

                    real_dates = list(set([r.date() for r in real_dates]))
                    real_dates.sort(key=lambda x: x)
                    real_date_dict = {}
                    for real_date in real_dates:
                        real_date_dict[real_date] = valuation_layer_to_be_sorted.filtered(
                            lambda x: x.real_date.date() == real_date)
                    print('real_date_dict', real_date_dict)
                    # for layer_to_change in date_to_change:
                    #     layer_to_change.real_date = date_to_change[layer_to_change]

                    for date in real_date_dict:
                        in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
                        print('in_layer--', in_layer)
                        return_out = real_date_dict[date].filtered(
                            lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
                        normal_out = real_date_dict[date].filtered(
                            lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
                        combine = in_layer + return_out + normal_out
                        print('combine', combine)
                        new_layers += combine
                    print('new_layers.....', new_layers)
                    out_layer_new = new_layers.filtered(
                        lambda x: (
                                          x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                                  first_layer[0].real_date)
                    print('before........', out_layers)
                    out_layers = out_layer_new
                    print('after-sort', out_layer_new)
                # f_layer = valuation_layers.filtered(lambda x: x.cost_adjustment_id == cost_adjustment)
                # if not f_layer:
                #     out_layers -= out_layers
                if out_layers:
                    for layer in out_layers:
                        layers = self.env['stock.valuation.layer']
                        print('********', layer)
                        for l in new_layers:
                            if l != layer:
                                layers += l
                            else:
                                break
                        if not layers:
                            if layer.stock_move_id.inventory_id and layer.value > 0:
                                continue
                            else:

                                user_error_case = True
                                break
                        landed_cost_revaluation_svl = valuation_layers_all.filtered(
                            lambda x: x.blank_type == 'Landed Cost' or x.blank_type == 'Revaluation')
                        print('landed_cost_revaluation_svl', landed_cost_revaluation_svl)
                        if landed_cost_revaluation_svl:
                            layers += landed_cost_revaluation_svl

                        unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                            layers.mapped('quantity')) != 0 else 0
                        print('unit_cost', unit_cost, sum(layers.mapped('value')), sum(layers.mapped('quantity')))
                        if unit_cost == 0:
                            continue
                        if layer.stock_move_id.origin_returned_move_id:
                            unit_cost = layer.stock_move_id.origin_returned_move_id.stock_valuation_layer_ids.unit_cost
                            print('..........u......', unit_cost, layer.stock_move_id.origin_returned_move_id,
                                  layer.stock_move_id.origin_returned_move_id.stock_valuation_layer_ids)

                        layer.unit_cost = unit_cost
                        actual_value = unit_cost * layer.quantity
                        layer.value = actual_value
                        print('LAYER', layer.value)
                        layer.account_move_id.button_draft()
                        credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                        credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                        debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                        debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                        print('LINE', credit_line.credit, debit_line.debit)
                        layer.account_move_id.action_post()
                    # if not user_error_case:
                    #     in_svl = valuation_layers_all.filtered(lambda
                    #                                                x: x.value > 0 and x.blank_type != 'Adjustment' and x.order_type == 'purchase' and x.margin != 0 and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                    #     print('in_svl---', in_svl)
                    #     if in_svl:
                    #         for svl in in_svl:
                    #             if not svl.account_move_id.has_reconciled_entries:
                    #                 svl.unit_cost = svl.invoiced_unit_price
                    #                 svl.value = svl.invoiced_amount
                    #                 print('svl.unit_cost', svl.unit_cost, svl.value)
                    #                 svl.account_move_id.button_draft()
                    #                 credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    #                 credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
                    #                 debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    #                 debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
                    #                 print('LINE', credit_line.credit, debit_line.debit)
                    #                 svl.account_move_id.action_post()
                    #                 out_layers = valuation_layers_all.filtered(
                    #                     lambda x: (
                    #                                       x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                    #                               svl.real_date).sorted(
                    #                     key=lambda x: x.real_date)
                    #                 print('out_layers..........', out_layers)
                    #                 for layer in out_layers:
                    #                     print('layer2-->>>', layer)
                    #                     layers = valuation_layers_all.filtered(
                    #                         lambda x: x.real_date <= layer.real_date)
                    #                     layers = layers - layer
                    #                     print('..........', layers)
                    #                     if not layers:
                    #                         break
                    #
                    #                     unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                    #                         layers.mapped('quantity')) != 0 else 0
                    #                     print('unit_cost7777', unit_cost, sum(layers.mapped('value')),
                    #                           sum(layers.mapped('quantity')))
                    #                     if unit_cost == 0:
                    #                         continue
                    #
                    #                     layer.unit_cost = unit_cost
                    #                     actual_value = unit_cost * layer.quantity
                    #                     layer.value = actual_value
                    #                     print('LAYER2', layer.value)
                    #                     layer.account_move_id.button_draft()
                    #                     credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    #                     credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                    #                     debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    #                     debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                    #                     print('LINE2', credit_line.credit, debit_line.debit)
                    #                     layer.account_move_id.action_post()

                # else:
                #     in_svl = valuation_layers_all.filtered(
                #         lambda x: x.value > 0 and x.margin != 0 and x.blank_type not in (
                #             'Adjustment', 'Landed Cost', 'Revaluation'))
                #
                #     if in_svl:
                #         for svl in in_svl:
                #             if not svl.account_move_id.has_reconciled_entries:
                #                 svl.unit_cost = svl.invoiced_unit_price
                #                 svl.value = svl.invoiced_amount
                #                 print('svl.unit_cost', svl.unit_cost, svl.value)
                #                 svl.account_move_id.button_draft()
                #                 credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                #                 credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
                #                 debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                #                 debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
                #                 print('LINE', credit_line.credit, debit_line.debit)
                #                 svl.account_move_id.action_post()
                #                 out_layers = valuation_layers_all.filtered(
                #                     lambda x: (
                #                                       x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                #                               svl.real_date).sorted(
                #                     key=lambda x: x.real_date)
                #                 for layer in out_layers:
                #                     print('layer2-->>>', layer)
                #                     layers = valuation_layers_all.filtered(
                #                         lambda x: x.real_date <= layer.real_date)
                #                     layers = layers - layer
                #                     print('..........', layers)
                #                     if not layers:
                #                         break
                #
                #                     unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                #                         layers.mapped('quantity')) != 0 else 0
                #                     print('unit_cost7777', unit_cost, sum(layers.mapped('value')),
                #                           sum(layers.mapped('quantity')))
                #
                #                     layer.unit_cost = unit_cost
                #                     actual_value = unit_cost * layer.quantity
                #                     layer.value = actual_value
                #                     print('LAYER2', layer.value)
                #                     layer.account_move_id.button_draft()
                #                     credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                #                     credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                #                     debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                #                     debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                #                     print('LINE2', credit_line.credit, debit_line.debit)
                #                     layer.account_move_id.action_post()
                #
                #     else:
                #         new_layers = self.env['stock.valuation.layer']
                #         out_layers = valuation_layers_all.filtered(
                #             lambda x: (
                #                               x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                #                       first_layer[
                #                           0].real_date).sorted(
                #             key=lambda x: x.real_date)
                #         real_dates = valuation_layer_to_be_sorted.mapped('real_date')
                #         real_dates = list(set([r.date() for r in real_dates]))
                #         real_dates.sort(key=lambda x: x)
                #         real_date_dict = {}
                #         for real_date in real_dates:
                #             real_date_dict[real_date] = valuation_layers_all.filtered(
                #                 lambda x: x.real_date.date() == real_date)
                #         print('real_date_dict', real_date_dict)
                #
                #         for date in real_date_dict:
                #             in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
                #             print('in_layer--', in_layer)
                #             return_out = real_date_dict[date].filtered(
                #                 lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
                #             normal_out = real_date_dict[date].filtered(
                #                 lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
                #             combine = in_layer + return_out + normal_out
                #             print('combine', combine)
                #             new_layers += combine
                #         print('new_layers.....', new_layers)
                #         out_layer_new = new_layers.filtered(
                #             lambda x: (
                #                               x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                #                       first_layer[0].real_date)
                #         print('before........', out_layers)
                #         out_layers = out_layer_new
                #         print('adjust2', out_layers)
                #         for layer in out_layers:
                #             layers = self.env['stock.valuation.layer']
                #             print('********', layer)
                #             for l in new_layers:
                #                 if l != layer:
                #                     layers += l
                #                 else:
                #                     break
                #             if not layers:
                #                 user_error_case = True
                #                 break
                #
                #             unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                #                 layers.mapped('quantity')) != 0 else 0
                #             print('unit_cost2', unit_cost, sum(layers.mapped('value')), sum(layers.mapped('quantity')))
                #
                #             layer.unit_cost = unit_cost
                #             actual_value = unit_cost * layer.quantity
                #             layer.value = actual_value
                #             print('LAYER2', layer.value)
                #             layer.account_move_id.button_draft()
                #             credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                #             credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                #             debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                #             debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                #             print('LINE2', credit_line.credit, debit_line.debit)
                #             layer.account_move_id.action_post()
                if return_layer:
                    for rl in return_layer:
                        return_svl = self.env['stock.valuation.layer'].search(
                            [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
                        print('initial', rl, rl.unit_cost, rl.value)
                        rl.unit_cost = return_svl.unit_cost
                        rl.value = return_svl.unit_cost * rl.quantity
                        print('---->', return_svl)
                        print('after---->', rl.unit_cost, rl.value)
                        rl.account_move_id.button_draft()
                        credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                        credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
                        debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                        debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
                        rl.account_move_id.action_post()
                if not user_error_case:
                    cost_adjustment.active = False
                    total_quantity = sum(valuation_layers_all.mapped('quantity'))
                    value1 = sum(valuation_layers_all.mapped('value'))
                    print('Price0,', value1 / total_quantity if total_quantity != 0 else 0)
                    cost_adjustment.product_id.with_context(
                        cost_adjustment=True).standard_price = value1 / total_quantity if total_quantity != 0 else 0

    def ca_adjust_confirm(self):
        print("ca_adjust_confirm", self)
        for cost_adjustment in self:
            valuation_layers_all = self.env['stock.valuation.layer'].search(
                [('product_id', '=', cost_adjustment.product_id.id), ('state', '=', 'confirm')])

            valuation_layers_all._compute_move_type()  # to_calculate_margin
            print("valuation_layers_all________", valuation_layers_all)
            valuation_layer_to_be_sorted = valuation_layers_all.filtered(
                lambda
                    x: x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            valuation_layers = valuation_layers_all.filtered(
                lambda
                    x: x.product_id == cost_adjustment.product_id and x.real_date < x.create_date and x.blank_type != 'Adjustment' and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            print('LLLLLLLLL', valuation_layers)
            return_layer = valuation_layers_all.filtered(lambda x: x.stock_move_id.origin_returned_move_id)

            out_layers = self.env['stock.valuation.layer']
            new_layers = self.env['stock.valuation.layer']
            if valuation_layers:
                first_layer = valuation_layers.sorted(key=lambda x: x.real_date)
                out_layers = valuation_layers_all.filtered(
                    lambda x: (
                                      x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                              first_layer[0].real_date).sorted(
                    key=lambda x: x.real_date)
                print('kkkkk', out_layers)
                real_dates = valuation_layer_to_be_sorted.mapped('real_date')
                real_dates = list(set([r.date() for r in real_dates]))
                real_dates.sort(key=lambda x: x)
                real_date_dict = {}
                for real_date in real_dates:
                    real_date_dict[real_date] = valuation_layer_to_be_sorted.filtered(
                        lambda x: x.real_date.date() == real_date)
                print('real_date_dict', real_date_dict)

                for date in real_date_dict:
                    in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
                    print('in_layer--', in_layer)
                    return_out = real_date_dict[date].filtered(
                        lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
                    normal_out = real_date_dict[date].filtered(
                        lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
                    combine = in_layer + return_out + normal_out
                    print('combine', combine)
                    new_layers += combine
                print('new_layers.....', new_layers)
                out_layer_new = new_layers.filtered(
                    lambda x: (
                                      x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                              first_layer[0].real_date)
                print('before........', out_layers)
                out_layers = out_layer_new
                print('after-sort', out_layer_new)
            f_layer = valuation_layers.filtered(lambda x: x.cost_adjustment_id == cost_adjustment)
            if not f_layer:
                out_layers -= out_layers
            print('out_layers.......', out_layers)
            if out_layers:
                for layer in out_layers:
                    layers = self.env['stock.valuation.layer']
                    print('********', layer)
                    for l in new_layers:
                        if l != layer:
                            layers += l
                        else:
                            break
                    print('layers....to_consider', layers)
                    landed_cost_revaluation_svl = valuation_layers_all.filtered(
                        lambda x: x.blank_type == 'Landed Cost' or x.blank_type == 'Revaluation')
                    print('landed_cost_revaluation_svl', landed_cost_revaluation_svl)
                    if landed_cost_revaluation_svl:
                        layers += landed_cost_revaluation_svl
                    if not layers:
                        if layer.stock_move_id.inventory_id and layer.value > 0:
                            continue
                        else:
                            raise UserError(
                                _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                    unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                        layers.mapped('quantity')) != 0 else 0
                    print('unit_cost', unit_cost, sum(layers.mapped('value')), sum(layers.mapped('quantity')))
                    if unit_cost == 0:
                        continue
                    if layer.stock_move_id.origin_returned_move_id:
                        unit_cost = layer.stock_move_id.origin_returned_move_id.stock_valuation_layer_ids.unit_cost
                        print('..........u......', unit_cost, layer.stock_move_id.origin_returned_move_id,
                              layer.stock_move_id.origin_returned_move_id.stock_valuation_layer_ids)

                    layer.unit_cost = unit_cost
                    actual_value = unit_cost * layer.quantity
                    layer.value = actual_value
                    print('LAYER', layer.value)
                    layer.account_move_id.button_draft()
                    credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                    debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                    print('LINE', credit_line.credit, debit_line.debit)
                    layer.account_move_id.action_post()
                in_svl = valuation_layers_all.filtered(lambda
                                                           x: x.value > 0 and x.blank_type != 'Adjustment' and x.order_type == 'purchase' and x.margin != 0 and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                print('in_svl---', in_svl)
                if in_svl:
                    for svl in in_svl:
                        if not svl.account_move_id.has_reconciled_entries:
                            svl.unit_cost = svl.invoiced_unit_price
                            svl.value = svl.invoiced_amount
                            print('svl.unit_cost', svl.unit_cost, svl.value)
                            svl.account_move_id.button_draft()
                            credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                            credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
                            debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                            debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
                            print('LINE', credit_line.credit, debit_line.debit)
                            svl.account_move_id.action_post()
                            out_layers = valuation_layers_all.filtered(
                                lambda x: (
                                                  x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                                          svl.real_date).sorted(
                                key=lambda x: x.real_date)
                            print('out_layers..........', out_layers)
                            for layer in out_layers:
                                print('layer2-->>>', layer)
                                layers = valuation_layers_all.filtered(
                                    lambda x: x.real_date <= layer.real_date)
                                layers = layers - layer
                                print('..........', layers)
                                if not layers:
                                    raise UserError(
                                        _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                                unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                                    layers.mapped('quantity')) != 0 else 0
                                print('unit_cost7777', unit_cost, sum(layers.mapped('value')),
                                      sum(layers.mapped('quantity')))
                                if unit_cost == 0:
                                    continue
                                layer.unit_cost = unit_cost
                                actual_value = unit_cost * layer.quantity
                                layer.value = actual_value
                                print('LAYER2', layer.value)
                                layer.account_move_id.button_draft()
                                credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                                credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                                debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                                debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                                print('LINE2', credit_line.credit, debit_line.debit)
                                layer.account_move_id.action_post()


            else:
                print('oooooooooooooooooooooooooo', valuation_layers_all)
                in_svl = valuation_layers_all.filtered(lambda x: x.value > 0 and x.margin != 0 and x.blank_type not in (
                    'Adjustment', 'Landed Cost', 'Revaluation'))

                if in_svl:
                    for svl in in_svl:
                        print('svl.unit_cost', svl, svl.unit_cost, svl.invoiced_unit_price, svl.value)

                        svl.unit_cost = svl.invoiced_unit_price
                        svl.value = svl.invoiced_amount
                        print('svl.unit_cost', svl.unit_cost, svl.value)
                        svl.account_move_id.button_draft()
                        credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                        credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
                        debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                        debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
                        print('LINE', credit_line.credit, debit_line.debit)
                        svl.account_move_id.action_post()
                        out_layers = valuation_layers_all.filtered(
                            lambda x: (
                                              x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                                      svl.real_date).sorted(
                            key=lambda x: x.real_date)
                        for layer in out_layers:
                            print('layer2-->>>', layer)
                            layers = valuation_layers_all.filtered(
                                lambda x: x.real_date <= layer.real_date)
                            layers = layers - layer
                            print('..........', layers)
                            if not layers:
                                raise UserError(
                                    _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                            unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                                layers.mapped('quantity')) != 0 else 0
                            print('unit_cost7777', unit_cost, sum(layers.mapped('value')),
                                  sum(layers.mapped('quantity')))
                            layer.unit_cost = unit_cost
                            actual_value = unit_cost * layer.quantity
                            layer.value = actual_value
                            print('LAYER2', layer.value)
                            layer.account_move_id.button_draft()
                            credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                            credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                            debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                            debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                            print('LINE2', credit_line.credit, debit_line.debit)
                            layer.account_move_id.action_post()

                else:
                    new_layers = self.env['stock.valuation.layer']
                    out_layers = valuation_layers_all.filtered(
                        lambda x: (
                                          x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                                  first_layer[
                                      0].real_date).sorted(
                        key=lambda x: x.real_date)
                    real_dates = valuation_layer_to_be_sorted.mapped('real_date')
                    real_dates = list(set([r.date() for r in real_dates]))
                    real_dates.sort(key=lambda x: x)
                    real_date_dict = {}
                    for real_date in real_dates:
                        real_date_dict[real_date] = valuation_layer_to_be_sorted.filtered(
                            lambda x: x.real_date.date() == real_date)
                    print('real_date_dict', real_date_dict)

                    for date in real_date_dict:
                        in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
                        print('in_layer--', in_layer)
                        return_out = real_date_dict[date].filtered(
                            lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
                        normal_out = real_date_dict[date].filtered(
                            lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
                        combine = in_layer + return_out + normal_out
                        print('combine', combine)
                        new_layers += combine
                    print('new_layers.....', new_layers)
                    out_layer_new = new_layers.filtered(
                        lambda x: (
                                          x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                                  first_layer[0].real_date)
                    print('before........', out_layers)
                    out_layers = out_layer_new
                    print('after-sort', out_layer_new)
                    print('adjust2', out_layers)
                    for layer in out_layers:
                        layers = self.env['stock.valuation.layer']
                        print('********', layer)
                        for l in new_layers:
                            if l != layer:
                                layers += l
                            else:
                                break
                        landed_cost_revaluation_svl = valuation_layers_all.filtered(
                            lambda x: x.blank_type == 'Landed Cost' or x.blank_type == 'Revaluation')
                        print('landed_cost_revaluation_svl', landed_cost_revaluation_svl)
                        if landed_cost_revaluation_svl:
                            layers += landed_cost_revaluation_svl
                        if not layers:
                            raise UserError(
                                _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                        unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                            layers.mapped('quantity')) != 0 else 0
                        print('unit_cost2', unit_cost, sum(layers.mapped('value')), sum(layers.mapped('quantity')))
                        layer.unit_cost = unit_cost
                        actual_value = unit_cost * layer.quantity
                        layer.value = actual_value
                        print('LAYER2', layer.value)
                        layer.account_move_id.button_draft()
                        credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                        credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                        debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                        debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                        print('LINE2', credit_line.credit, debit_line.debit)
                        layer.account_move_id.action_post()
            if return_layer:
                for rl in return_layer:
                    return_svl = self.env['stock.valuation.layer'].search(
                        [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
                    print('initial', rl, rl.unit_cost, rl.value)
                    rl.unit_cost = return_svl.unit_cost
                    rl.value = return_svl.unit_cost * rl.quantity
                    print('---->', return_svl)
                    print('after---->', rl.unit_cost, rl.value)
                    rl.account_move_id.button_draft()
                    credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
                    debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
                    rl.account_move_id.action_post()
            cost_adjustment.active = False
            total_quantity = sum(valuation_layers_all.mapped('quantity'))
            print('hhhhhhhh', total_quantity)
            value1 = sum(valuation_layers_all.mapped('value'))
            print('kkkkkkkkkkkkk', value1, total_quantity)
            print('Price0,', value1 / total_quantity if total_quantity != 0 else 0)
            cost_adjustment.product_id.with_context(
                cost_adjustment=True).standard_price = value1 / total_quantity if total_quantity != 0 else 0


class CostAdjustWarning(models.TransientModel):
    _name = 'cost.adjust.warning'
    _description = 'Cost Adjustment Warning'

    def confirm(self):
        cost_adjustments = self.env['cost.adjustments'].search([('id', 'in', self.env.context.get('active_ids'))])
        for cost_adjustment in cost_adjustments:
            valuation_layers_all = self.env['stock.valuation.layer'].search(
                [('product_id', '=', cost_adjustment.product_id.id), ('state', '=', 'confirm')]).sorted(
                key=lambda x: x.real_date)
            print('valuation_layers_all', valuation_layers_all)
            valuation_layer_to_be_sorted = valuation_layers_all.filtered(
                lambda
                    x: x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            valuation_layers = valuation_layers_all.filtered(
                lambda
                    x: x.product_id == cost_adjustment.product_id and x.real_date < x.create_date and x.blank_type != 'Adjustment' and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            print('LLLLLLLLL', valuation_layers)
            out_layers = self.env['stock.valuation.layer']
            return_layer = valuation_layers_all.filtered(lambda x: x.stock_move_id.origin_returned_move_id)
            print('return_layer.....', return_layer)
            new_layers = self.env['stock.valuation.layer']
            if valuation_layers:
                first_layer = valuation_layers.sorted(key=lambda x: x.real_date)
                out_layers = valuation_layers_all.filtered(
                    lambda x: (
                                      x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                              first_layer[0].real_date).sorted(
                    key=lambda x: x.real_date)

                real_dates = valuation_layer_to_be_sorted.mapped('real_date')
                print('...........dates', real_dates)
                real_dates = list(set([r.date() for r in real_dates]))
                real_dates.sort(key=lambda x: x)
                real_date_dict = {}
                for real_date in real_dates:
                    real_date_dict[real_date] = valuation_layer_to_be_sorted.filtered(
                        lambda x: x.real_date.date() == real_date)
                print('real_date_dict11', real_date_dict)

                # for layer_to_change in date_to_change:
                #     layer_to_change.real_date = date_to_change[layer_to_change]
                for date in real_date_dict:
                    in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
                    print('in_layer--', in_layer)
                    return_out = real_date_dict[date].filtered(
                        lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
                    normal_out = real_date_dict[date].filtered(
                        lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
                    combine = in_layer + return_out + normal_out
                    print('combine', combine)
                    new_layers += combine
                print('new_layers.....', new_layers)
                out_layer_new = new_layers.filtered(
                    lambda x: (
                                      x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                              first_layer[0].real_date)
                print('before........', out_layers)
                out_layers = out_layer_new
                print('after-sort', out_layer_new)

            # FIXME: below portions are commented for now as svl layer unit cost updated automatically with VB
            # f_layer = valuation_layers.filtered(lambda x: x.cost_adjustment_id == cost_adjustment)
            # if not f_layer:
            #     out_layers -= out_layers
            # print('OUT_LAYER_LAST....', out_layers)
            # FIXME: above portions are commented for now
            if out_layers:
                for layer in out_layers:
                    layers = self.env['stock.valuation.layer']
                    print('********', layer)
                    for l in new_layers:
                        if l != layer:
                            layers += l
                        else:
                            break
                    print('layers....', layers)

                    return_svl = layers.filtered(
                        lambda x: x.stock_move_id.origin_returned_move_id == layer.stock_move_id)
                    if return_svl:
                        layers = layers - return_svl
                    print('layers....1', layers)
                    landed_cost_revaluation_svl = valuation_layers_all.filtered(
                        lambda x: x.blank_type == 'Landed Cost' or x.blank_type == 'Revaluation')
                    print('landed_cost_revaluation_svl', landed_cost_revaluation_svl)
                    if landed_cost_revaluation_svl:
                        layers += landed_cost_revaluation_svl
                    if return_layer:
                        for rl in return_layer:
                            return_svl = self.env['stock.valuation.layer'].search(
                                [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
                            print('initial', rl, rl.unit_cost, rl.value)
                            rl.unit_cost = return_svl.unit_cost
                            rl.value = return_svl.unit_cost * rl.quantity
                            print('---->', return_svl)
                            print('after---->', rl.unit_cost, rl.value)
                            rl.account_move_id.button_draft()
                            credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                            credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
                            debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                            debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
                    if not layers:
                        if layer.stock_move_id.inventory_id and layer.value > 0:
                            continue
                        else:
                            raise UserError(
                                _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                    unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                        layers.mapped('quantity')) != 0 else 0
                    print('unit_cost111', layer, unit_cost, sum(layers.mapped('value')), sum(layers.mapped('quantity')))
                    if unit_cost == 0:
                        continue
                    if layer.stock_move_id.origin_returned_move_id:
                        unit_cost = layer.stock_move_id.origin_returned_move_id.stock_valuation_layer_ids.unit_cost

                    layer.unit_cost = unit_cost
                    actual_value = unit_cost * layer.quantity
                    layer.value = actual_value
                    print('LAYER', layer.value)
                    layer.account_move_id.button_draft()
                    credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                    debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                    print('LINE', credit_line.credit, debit_line.debit)
                    layer.account_move_id.action_post()
                # FIXME: below portions are commented for now
                # in_svl = valuation_layers_all.filtered(lambda
                #                                            x: x.value > 0 and x.blank_type != 'Adjustment' and x.order_type == 'purchase' and x.margin != 0 and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                # if in_svl:
                #     for svl in in_svl:
                #         if not svl.account_move_id.has_reconciled_entries:
                #             svl.unit_cost = svl.invoiced_unit_price
                #             svl.value = svl.invoiced_amount
                #             print('svl.unit_cost', svl.unit_cost, svl.value)
                #             svl.account_move_id.button_draft()
                #             credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                #             credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
                #             debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                #             debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
                #             svl.account_move_id.action_post()
                #             out_layers = valuation_layers_all.filtered(
                #                 lambda x: (
                #                                   x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                #                           svl.real_date).sorted(
                #                 key=lambda x: x.real_date)
                #             for layer in out_layers:
                #                 layers = valuation_layers_all.filtered(
                #                     lambda x: x.real_date <= layer.real_date)
                #                 layers = layers - layer
                #                 if not layers:
                #                     raise UserError(
                #                         _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                #                 unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                #                     layers.mapped('quantity')) != 0 else 0
                #                 if unit_cost == 0:
                #                     continue
                #                 layer.unit_cost = unit_cost
                #                 actual_value = unit_cost * layer.quantity
                #                 layer.value = actual_value
                #                 print('LAYER2', layer.value)
                #                 layer.account_move_id.button_draft()
                #                 credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                #                 credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                #                 debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                #                 debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                #                 print('LINE2', credit_line.credit, debit_line.debit)
                #                 layer.account_move_id.action_post()
                # FIXME: above portions are commented for now
            # FIXME: below portions are commented for now as svl unit cost is updated automatically with VB
            # else:
            #     in_svl = valuation_layers_all.filtered(lambda
            #                                                x: x.value > 0 and x.blank_type != 'Adjustment' and x.order_type == 'purchase' and x.margin != 0 and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            #     new_layers = self.env['stock.valuation.layer']
            #     out_layers = valuation_layers_all.filtered(
            #         lambda x: (
            #                           x.value < 0 or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
            #                   first_layer[
            #                       0].real_date).sorted(
            #         key=lambda x: x.real_date)
            #     real_dates = valuation_layer_to_be_sorted.mapped('real_date')
            #     real_dates = list(set([r.date() for r in real_dates]))
            #     real_dates.sort(key=lambda x: x)
            #     real_date_dict = {}
            #     for real_date in real_dates:
            #         real_date_dict[real_date] = valuation_layers_all.filtered(
            #             lambda x: x.real_date.date() == real_date)
            #     print('real_date_dict22', real_date_dict)
            #     for date in real_date_dict:
            #         in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
            #         print('in_layer--', in_layer)
            #         return_out = real_date_dict[date].filtered(
            #             lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
            #         normal_out = real_date_dict[date].filtered(
            #             lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
            #         combine = in_layer + return_out + normal_out
            #         print('combine', combine)
            #         new_layers += combine
            #     print('new_layers.....', new_layers, )
            #
            #     out_layer_new = new_layers.filtered(
            #         lambda x: (
            #                           x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
            #                   first_layer[0].real_date)
            #     print('before........x', out_layers)
            #     out_layers = out_layer_new
            #     print('after-sort', out_layer_new)
            #
            #     for layer in out_layers:
            #         layers = self.env['stock.valuation.layer']
            #         print('********', layer)
            #         for l in new_layers:
            #             print('L', l, l.value)
            #             if l != layer:
            #                 layers += l
            #             else:
            #                 break
            #         if return_layer:
            #             for rl in return_layer:
            #                 return_svl = self.env['stock.valuation.layer'].search(
            #                     [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
            #                 print('initial', rl, rl.unit_cost, rl.value)
            #                 rl.unit_cost = return_svl.unit_cost
            #                 rl.value = return_svl.unit_cost * rl.quantity
            #                 print('return-after---->', rl, rl.unit_cost, rl.value)
            #                 rl.account_move_id.button_draft()
            #                 credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
            #                 credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
            #                 debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
            #                 debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
            #         print('layers_to_consider....11', layers)
            #         if not layers:
            #             raise UserError(
            #                 _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
            #         unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
            #             layers.mapped('quantity')) != 0 else 0
            #         print('unit_cost....2', layer, unit_cost, sum(layers.mapped('value')),
            #               sum(layers.mapped('quantity')))
            #
            #         layer.unit_cost = unit_cost
            #         actual_value = unit_cost * layer.quantity
            #         layer.value = actual_value
            #         print('Value......2', layer, layer.value)
            #         layer.account_move_id.button_draft()
            #         credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
            #         credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
            #         debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
            #         debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
            #         layer.account_move_id.action_post()

            if return_layer:
                for rl in return_layer:
                    return_svl = self.env['stock.valuation.layer'].search(
                        [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
                    print('initial', rl, rl.unit_cost, rl.value)
                    rl.unit_cost = return_svl.unit_cost
                    rl.value = return_svl.unit_cost * rl.quantity
                    print('---->', return_svl)
                    print('after---->', rl.unit_cost, rl.value)
                    rl.account_move_id.button_draft()
                    credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
                    debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
                    rl.account_move_id.action_post()
            cost_adjustment.active = False
            total_quantity = sum(valuation_layers_all.mapped('quantity'))
            value1 = sum(valuation_layers_all.mapped('value'))
            print('value1', value1)
            cost_adjustment.product_id.with_context(
                cost_adjustment=True).standard_price = value1 / total_quantity if total_quantity != 0 else 0


class CostAdjustWizard(models.TransientModel):
    _name = 'cost.adjust.wizard'
    _description = 'Cost Adjustment Wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    def confirm_adjust(self):
        if self.env.context.get('active_model') == 'product.template':
            product_template = self.env['product.template'].browse(self.env.context.get('active_id'))
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template.id)])
            print('product_id..temp', product_id)
        else:
            product_id = self.env['product.product'].browse(self.env.context.get('active_id'))
            print('product_id..', product_id)

        cost_adjustment = self.env['cost.adjustments'].search([('product_id', '=', product_id.id)])
        if not cost_adjustment:
            raise UserError(_('Nothing To Adjust!'))
        else:
            self.adjust_with_date(cost_adjustment, self.date_from, self.date_to)

    def adjust_with_date(self, ca, from_date, to_date):
        # ca = self.env['cost.adjustments'].search([('id', 'in', self.env.context.get('active_ids'))])
        for cost_adjustment in ca:
            valuation_layers_all = self.env['stock.valuation.layer'].search(
                [('product_id', '=', cost_adjustment.product_id.id), ('state', '=', 'confirm')]).sorted(
                key=lambda x: x.real_date)
            all_layer = valuation_layers_all
            valuation_layer_to_be_sorted = valuation_layers_all.filtered(
                lambda
                    x: x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            print('valuation_layers_all', valuation_layers_all)
            if to_date:
                valuation_layers_all = valuation_layers_all.filtered(
                    lambda x: x.real_date.date() <= to_date)

            valuation_layers = valuation_layers_all.filtered(
                lambda
                    x: x.product_id == cost_adjustment.product_id and x.real_date < x.create_date and x.blank_type != 'Adjustment' and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            print('LLLLLLLLL', valuation_layers)
            out_layers = self.env['stock.valuation.layer']
            all_layer_to_correct = self.env['stock.valuation.layer']
            return_layer = valuation_layers_all.filtered(lambda x: x.stock_move_id.origin_returned_move_id)
            print('return_layer.....', return_layer)
            new_layers = self.env['stock.valuation.layer']
            if valuation_layers:
                first_layer = valuation_layers.sorted(key=lambda x: x.real_date)
                out_layers = valuation_layers_all.filtered(
                    lambda x: (
                                      x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                              first_layer[0].real_date).sorted(
                    key=lambda x: x.real_date)
                all_layer_to_correct = all_layer.filtered(
                    lambda x: (
                                      x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                              first_layer[0].real_date).sorted(
                    key=lambda x: x.real_date)

                real_dates = valuation_layer_to_be_sorted.mapped('real_date')
                # real_date_new = []
                # date_to_change = {}
                # for layer in valuation_layers_all:
                #     time = datetime.strptime(str(layer.real_date), "%Y-%m-%d %H:%M:%S")
                #     print('time......', time, time.hour, time.min, time.second)
                #     if time.hour == 18 and time.minute == 30 and time.second == 00:
                #         date_to_change[layer] = layer.real_date
                #         layer.real_date += timedelta(days=1)
                #         print('date.....inc', layer.real_date)
                #     real_date_new.append(layer.real_date)
                # real_dates = real_date_new
                real_dates = list(set([r.date() for r in real_dates]))
                real_dates.sort(key=lambda x: x)
                real_date_dict = {}
                for real_date in real_dates:
                    real_date_dict[real_date] = valuation_layer_to_be_sorted.filtered(
                        lambda x: x.real_date.date() == real_date)
                print('real_date_dict', real_date_dict)
                for date in real_date_dict:
                    in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
                    print('in_layer--', in_layer)
                    return_out = real_date_dict[date].filtered(
                        lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
                    normal_out = real_date_dict[date].filtered(
                        lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
                    combine = in_layer + return_out + normal_out
                    print('combine', combine)
                    new_layers += combine
                print('new_layers.....', new_layers)
                out_layer_new = new_layers.filtered(
                    lambda x: (
                                      x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                              first_layer[0].real_date)
                print('before........', out_layers)
                out_layers = out_layer_new
                print('after-sort', out_layer_new)

            # f_layer = valuation_layers.filtered(lambda x: x.cost_adjustment_id == cost_adjustment)
            # if not f_layer:
            #     out_layers -= out_layers
            if out_layers:
                for layer in out_layers:
                    layers = self.env['stock.valuation.layer']
                    print('********', layer)
                    for l in new_layers:
                        if l != layer:
                            layers += l
                        else:
                            break
                    print('layers....', layers)
                    # layers = valuation_layers_all.filtered(
                    #     lambda
                    #         x: x.real_date <= layer.real_date)  ###new_change( and x.value > 0) 14/03/2022
                    # layers = layers - layer
                    return_svl = layers.filtered(
                        lambda x: x.stock_move_id.origin_returned_move_id == layer.stock_move_id)
                    if return_svl:
                        layers = layers - return_svl
                    print('layers....1', layers)
                    landed_cost_revaluation_svl = valuation_layers_all.filtered(
                        lambda x: x.blank_type == 'Landed Cost' or x.blank_type == 'Revaluation')
                    print('landed_cost_revaluation_svl', landed_cost_revaluation_svl)
                    if landed_cost_revaluation_svl:
                        layers += landed_cost_revaluation_svl
                    if return_layer:
                        for rl in return_layer:
                            return_svl = self.env['stock.valuation.layer'].search(
                                [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
                            print('initial', rl, rl.unit_cost, rl.value)
                            rl.unit_cost = return_svl.unit_cost
                            rl.value = return_svl.unit_cost * rl.quantity
                            print('---->', return_svl)
                            print('after---->', rl.unit_cost, rl.value)
                            rl.account_move_id.button_draft()
                            credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                            credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
                            debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                            debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
                    if not layers:
                        if layer.stock_move_id.inventory_id and layer.value > 0:
                            continue
                        else:
                            raise UserError(
                                _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                    unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                        layers.mapped('quantity')) != 0 else 0
                    print('unit_cost111', unit_cost, sum(layers.mapped('value')), sum(layers.mapped('quantity')))
                    if unit_cost == 0:
                        continue
                    if layer.stock_move_id.origin_returned_move_id:
                        unit_cost = layer.stock_move_id.origin_returned_move_id.stock_valuation_layer_ids.unit_cost

                    layer.unit_cost = unit_cost
                    actual_value = unit_cost * layer.quantity
                    layer.value = actual_value
                    print('LAYER', layer.value)
                    layer.account_move_id.button_draft()
                    credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                    debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                    print('LINE', credit_line.credit, debit_line.debit)
                    layer.account_move_id.action_post()
                # in_svl = valuation_layers_all.filtered(lambda
                #                                            x: x.value > 0 and x.blank_type != 'Adjustment' and x.order_type == 'purchase' and x.margin != 0 and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
                # if in_svl:
                #     for svl in in_svl:
                #         if not svl.account_move_id.has_reconciled_entries:
                #             svl.unit_cost = svl.invoiced_unit_price
                #             svl.value = svl.invoiced_amount
                #             print('svl.unit_cost', svl.unit_cost, svl.value)
                #             svl.account_move_id.button_draft()
                #             credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                #             credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
                #             debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                #             debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
                #             svl.account_move_id.action_post()
                #             out_layers = valuation_layers_all.filtered(
                #                 lambda x: (
                #                                   x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
                #                           svl.real_date).sorted(
                #                 key=lambda x: x.real_date)
                #             for layer in out_layers:
                #                 layers = valuation_layers_all.filtered(
                #                     lambda x: x.real_date <= layer.real_date)
                #                 layers = layers - layer
                #                 if not layers:
                #                     raise UserError(
                #                         _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
                #                 unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
                #                     layers.mapped('quantity')) != 0 else 0
                #                 if unit_cost == 0:
                #                     continue
                #                 # if layer[3]:
                #                 #     print('check',layer[3])
                #                 layer.unit_cost = unit_cost
                #                 actual_value = unit_cost * layer.quantity
                #                 layer.value = actual_value
                #                 print('LAYER2', layer.value)
                #                 layer.account_move_id.button_draft()
                #                 credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                #                 credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
                #                 debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                #                 debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
                #                 print('LINE2', credit_line.credit, debit_line.debit)
                #                 layer.account_move_id.action_post()

            # else:
            #     in_svl = valuation_layers_all.filtered(lambda
            #                                                x: x.value > 0 and x.blank_type != 'Adjustment' and x.order_type == 'purchase' and x.margin != 0 and x.blank_type != 'Landed Cost' and x.blank_type != 'Revaluation')
            #     if in_svl:
            #         for svl in in_svl:
            #             if not svl.account_move_id.has_reconciled_entries:
            #                 svl.unit_cost = svl.invoiced_unit_price
            #                 svl.value = svl.invoiced_amount
            #                 svl.account_move_id.button_draft()
            #                 credit_line = svl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
            #                 credit_line.with_context(check_move_validity=False).credit = abs(svl.value)
            #                 debit_line = svl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
            #                 debit_line.with_context(check_move_validity=False).debit = abs(svl.value)
            #                 svl.account_move_id.action_post()
            #                 out_layers = valuation_layers_all.filtered(
            #                     lambda x: (
            #                                       x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
            #                               svl.real_date).sorted(
            #                     key=lambda x: x.real_date)
            #                 for layer in out_layers:
            #                     layers = valuation_layers_all.filtered(
            #                         lambda x: x.real_date <= layer.real_date)
            #                     layers = layers - layer
            #                     if not layers:
            #                         raise UserError(
            #                             _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
            #                     unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
            #                         layers.mapped('quantity')) != 0 else 0
            #                     # if layer[3]:
            #                     #     print('check',layer[3])
            #                     layer.unit_cost = unit_cost
            #                     actual_value = unit_cost * layer.quantity
            #                     layer.value = actual_value
            #                     layer.account_move_id.button_draft()
            #                     credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
            #                     credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
            #                     debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
            #                     debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
            #                     layer.account_move_id.action_post()
            #     else:
            #         new_layers = self.env['stock.valuation.layer']
            #         out_layers = valuation_layers_all.filtered(
            #             lambda x: (
            #                               x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
            #                       first_layer[
            #                           0].real_date).sorted(
            #             key=lambda x: x.real_date)
            #         real_dates = valuation_layer_to_be_sorted.mapped('real_date')
            #         real_dates = list(set([r.date() for r in real_dates]))
            #         real_dates.sort(key=lambda x: x)
            #         real_date_dict = {}
            #         for real_date in real_dates:
            #             real_date_dict[real_date] = valuation_layers_all.filtered(
            #                 lambda x: x.real_date.date() == real_date)
            #         print('real_date_dict22', real_date_dict)
            #
            #         for date in real_date_dict:
            #             in_layer = real_date_dict[date].filtered(lambda x: x.value > 0)
            #             print('in_layer--', in_layer)
            #             return_out = real_date_dict[date].filtered(
            #                 lambda x: x.stock_move_id._is_out() and x.stock_move_id.origin_returned_move_id)
            #             normal_out = real_date_dict[date].filtered(
            #                 lambda x: x.stock_move_id._is_out() and not x.stock_move_id.origin_returned_move_id)
            #             combine = in_layer + return_out + normal_out
            #             print('combine', combine)
            #             new_layers += combine
            #         print('new_layers.....', new_layers)
            #         out_layer_new = new_layers.filtered(
            #             lambda x: (
            #                               x.stock_move_id._is_out() or x.is_manual_receipt == True or x.stock_move_id.inventory_id) and x.real_date >=
            #                       first_layer[0].real_date)
            #         print('before........', out_layers)
            #         out_layers = out_layer_new
            #         print('after-sort', out_layer_new)
            #         for layer in out_layers:
            #             layers = self.env['stock.valuation.layer']
            #             print('********', layer)
            #             for l in new_layers:
            #                 if l != layer:
            #                     layers += l
            #                 else:
            #                     break
            #             if return_layer:
            #                 for rl in return_layer:
            #                     return_svl = self.env['stock.valuation.layer'].search(
            #                         [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
            #                     print('initial', rl, rl.unit_cost, rl.value)
            #                     rl.unit_cost = return_svl.unit_cost
            #                     rl.value = return_svl.unit_cost * rl.quantity
            #                     print('---->', return_svl)
            #                     print('after---->', rl.unit_cost, rl.value)
            #                     rl.account_move_id.button_draft()
            #                     credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
            #                     credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
            #                     debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
            #                     debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
            #             print('layers....to_consider', layers)
            #             if not layers:
            #                 raise UserError(
            #                     _('You need to register a Inventory Receipt with a Real Date on the same date or before the Real Date of the Delivery or you need to change the Real Date of the Delivery Order'))
            #             unit_cost = sum(layers.mapped('value')) / sum(layers.mapped('quantity')) if sum(
            #                 layers.mapped('quantity')) != 0 else 0
            #             # if layer[3]:
            #             #     print('check',layer[3])
            #             layer.unit_cost = unit_cost
            #             actual_value = unit_cost * layer.quantity
            #             layer.value = actual_value
            #             layer.account_move_id.button_draft()
            #             credit_line = layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
            #             credit_line.with_context(check_move_validity=False).credit = abs(actual_value)
            #             debit_line = layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
            #             debit_line.with_context(check_move_validity=False).debit = abs(actual_value)
            #             layer.account_move_id.action_post()

            if return_layer:
                for rl in return_layer:
                    return_svl = self.env['stock.valuation.layer'].search(
                        [('stock_move_id', '=', rl.stock_move_id.origin_returned_move_id.id)])
                    print('initial', rl, rl.unit_cost, rl.value)
                    rl.unit_cost = return_svl.unit_cost
                    rl.value = return_svl.unit_cost * rl.quantity
                    print('---->', return_svl)
                    print('after---->', rl.unit_cost, rl.value)
                    rl.account_move_id.button_draft()
                    credit_line = rl.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                    credit_line.with_context(check_move_validity=False).credit = abs(rl.value)
                    debit_line = rl.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                    debit_line.with_context(check_move_validity=False).debit = abs(rl.value)
                    rl.account_move_id.action_post()
            if len(all_layer_to_correct - out_layers) == 0:
                cost_adjustment.active = False
            total_quantity = sum(valuation_layers_all.mapped('quantity'))
            value1 = sum(valuation_layers_all.mapped('value'))
            cost_adjustment.product_id.with_context(
                cost_adjustment=True).standard_price = value1 / total_quantity if total_quantity != 0 else 0
