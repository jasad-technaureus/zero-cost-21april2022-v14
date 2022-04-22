# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import models, fields, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        purchase_id = None
        for line in self.invoice_line_ids:
            purchase_id = line.purchase_line_id.order_id
            purchase_line = line.purchase_line_id.order_id.order_line.filtered(lambda x: x == line.purchase_line_id)

            if purchase_line and purchase_line.price_unit != line.price_unit and purchase_id.currency_id == self.currency_id:
                # products = self.env['cost.adjustments'].search([('product_id', '=', line.product_id.id)])
                # print('products', products)
                if purchase_id.picking_ids:
                    picking_ids = purchase_id.picking_ids
                    picking_ids = picking_ids.filtered(lambda x: x.state == 'done')
                    if picking_ids:
                        for line in self.line_ids:
                            move = picking_ids[0].move_lines.filtered(
                                lambda x: x.purchase_line_id == line.purchase_line_id)
                            if move:
                                valuation_layer = self.env['stock.valuation.layer'].search(
                                    [('stock_move_id', '=', move.id)])
                                print('unitcost...........', line.price_unit)
                                if valuation_layer.unit_cost != line.price_unit:
                                    valuation_layer.unit_cost = line.price_unit
                                    valuation_layer.value = valuation_layer.unit_cost * valuation_layer.quantity
                                    # valuation_layer.unit_cost = valuation_layer.value / valuation_layer.quantity
                                    valuation_layer.account_move_id.button_draft()
                                    valuation_layer.account_move_id.button_draft()
                                    credit_line = valuation_layer.account_move_id.line_ids.filtered(
                                        lambda x: x.credit > 0)
                                    credit_line.with_context(check_move_validity=False).credit = abs(
                                        valuation_layer.value)
                                    debit_line = valuation_layer.account_move_id.line_ids.filtered(
                                        lambda x: x.debit > 0)
                                    debit_line.with_context(check_move_validity=False).debit = abs(
                                        valuation_layer.value)
                                    valuation_layer.account_move_id.action_post()
                                    print('UNITCOST...', valuation_layer.unit_cost)
                # if not products:
                #     cost_adjustment = self.env['cost.adjustments'].create({'product_id': line.product_id.id,
                #                                                            'is_from_bll': True})
                #     cost_adjustment.ca_adjust_confirm()
                # else:
                #     products.ca_adjust_confirm()
        if purchase_id:
            if purchase_id.currency_id != purchase_id.company_id.currency_id:
                if self.currency_id != self.company_id.currency_id:
                    # purchase_rate = 1 / purchase_id.currency_rate
                    purchase_rate = purchase_id.currency_id.rate
                    bill_rate = self.main_curr_rate
                    bill_rate = 1 / bill_rate
                    print('RATE..........', round(purchase_rate, 5), round(bill_rate, 5))
                    if round(purchase_rate, 5) != round(bill_rate, 5):
                        bill_product_ids = self.invoice_line_ids.mapped('product_id').ids
                        products = self.env['cost.adjustments'].search(
                            [('product_id', 'in', bill_product_ids)])
                        if purchase_id.picking_ids:
                            picking_ids = purchase_id.picking_ids
                            picking_ids = picking_ids.filtered(lambda x: x.state == 'done')
                            if picking_ids:
                                for line in self.line_ids:
                                    for picking in picking_ids:
                                        move = picking.move_lines.filtered(
                                            lambda x: x.purchase_line_id == line.purchase_line_id)
                                        move = move.filtered(lambda x: x.state == 'done')
                                        print('move.......')
                                        if move:
                                            valuation_layer = self.env['stock.valuation.layer'].search(
                                                [('stock_move_id', '=', move.id)])
                                            print('line.....', line.debit)
                                            print('-----', valuation_layer.unit_cost, valuation_layer.invoiced_unit_price)
                                            if valuation_layer.unit_cost != valuation_layer.invoiced_unit_price:
                                                unit_price = line.debit / line.quantity
                                                value = unit_price * move.product_uom_qty
                                                valuation_layer.value = value
                                                print('ssssssssssss', value,move.product_uom_qty,unit_price)
                                                valuation_layer.unit_cost = valuation_layer.value / valuation_layer.quantity
                                                valuation_layer.account_move_id.button_draft()
                                                credit_line = valuation_layer.account_move_id.line_ids.filtered(
                                                    lambda x: x.credit > 0)
                                                credit_line.with_context(check_move_validity=False).credit = abs(
                                                    valuation_layer.value)
                                                debit_line = valuation_layer.account_move_id.line_ids.filtered(
                                                    lambda x: x.debit > 0)
                                                debit_line.with_context(check_move_validity=False).debit = abs(
                                                    valuation_layer.value)
                                                valuation_layer.account_move_id.action_post()
                                            else:
                                                valuation_layer.value = line.debit
                                                valuation_layer.unit_cost = valuation_layer.value / valuation_layer.quantity
                                                valuation_layer.account_move_id.button_draft()
                                                credit_line = valuation_layer.account_move_id.line_ids.filtered(
                                                    lambda x: x.credit > 0)
                                                credit_line.with_context(check_move_validity=False).credit = abs(
                                                    valuation_layer.value)
                                                debit_line = valuation_layer.account_move_id.line_ids.filtered(
                                                    lambda x: x.debit > 0)
                                                debit_line.with_context(check_move_validity=False).debit = abs(
                                                    valuation_layer.value)
                                                valuation_layer.account_move_id.action_post()

                        # if not products:
                        #     for product in bill_product_ids:
                        #         cost_adjustment = self.env['cost.adjustments'].create(
                        #             {'product_id': product})
                        #         saillll
                        #         cost_adjustment.ca_adjust_confirm()

                        # else:
                        #     products = list(set(bill_product_ids) - set(products.mapped('product_id').ids))
                        #     for product in products:
                        #         cost_adjustment = self.env['cost.adjustments'].create(
                        #             {'product_id': product})
                        #         print('cost_adjustment-created2', cost_adjustment)
                        #         cost_adjustment.ca_adjust_confirm()
                    else:
                        if purchase_id.picking_ids:

                            picking_ids = purchase_id.picking_ids
                            for line in self.line_ids:
                                move = picking_ids[0].move_lines.filtered(
                                    lambda x: x.purchase_line_id == line.purchase_line_id)
                                move = move.filtered(lambda x: x.state == 'done')
                                if move:
                                    valuation_layer = self.env['stock.valuation.layer'].search(
                                        [('stock_move_id', '=', move.id)])
                                    print('line.....fff', line.debit)
                                    valuation_layer.value = line.debit
                                    valuation_layer.unit_cost = valuation_layer.value / valuation_layer.quantity
                                    valuation_layer.account_move_id.button_draft()
                                    credit_line = valuation_layer.account_move_id.line_ids.filtered(
                                        lambda x: x.credit > 0)
                                    credit_line.with_context(check_move_validity=False).credit = abs(
                                        valuation_layer.value)
                                    debit_line = valuation_layer.account_move_id.line_ids.filtered(
                                        lambda x: x.debit > 0)
                                    debit_line.with_context(check_move_validity=False).debit = abs(
                                        valuation_layer.value)
                                    print('LINE...', credit_line.credit, debit_line.debit)
                                    # valuation_layer.account_move_id.action_post()
                                    # credit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                                    # print('llllllllllll')
                                    # credit_line.reconciled = False
                                    # credit_line.matched_debit_ids = False
                                    # credit_line.with_context(check_move_validity=False).credit = abs(valuation_layer.value)
                                    # debit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                                    # debit_line.reconciled = False
                                    # debit_line.matched_debit_ids = False
                                    # debit_line.with_context(check_move_validity=False).debit = abs(valuation_layer.value)
                                    print('LINE', credit_line.credit, debit_line.debit)
                                    valuation_layer.account_move_id.action_post()

            if purchase_id.currency_id != self.currency_id:
                if purchase_id.picking_ids:
                    picking_ids = purchase_id.picking_ids
                    for line in self.line_ids:
                        move = picking_ids[0].move_lines.filtered(
                            lambda x: x.purchase_line_id == line.purchase_line_id)
                        print('move...', move)
                        if move:
                            valuation_layer = self.env['stock.valuation.layer'].search(
                                [('stock_move_id', '=', move.id)])
                            print('line.....', line.debit)
                            valuation_layer.value = line.debit
                            valuation_layer.unit_cost = valuation_layer.value / valuation_layer.quantity if valuation_layer.quantity != 0 else 0
                            valuation_layer.account_move_id.button_draft()
                            credit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                            credit_line.with_context(check_move_validity=False).credit = abs(valuation_layer.value)
                            debit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                            debit_line.with_context(check_move_validity=False).debit = abs(valuation_layer.value)
                            print('LINE...', credit_line.credit, debit_line.debit)
                            # valuation_layer.account_move_id.action_post()
                            # credit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                            # print('llllllllllll')
                            # credit_line.reconciled = False
                            # credit_line.matched_debit_ids = False
                            # credit_line.with_context(check_move_validity=False).credit = abs(valuation_layer.value)
                            # debit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                            # debit_line.reconciled = False
                            # debit_line.matched_debit_ids = False
                            # debit_line.with_context(check_move_validity=False).debit = abs(valuation_layer.value)
                            print('LINE', credit_line.credit, debit_line.debit)
                            valuation_layer.account_move_id.action_post()

        if self.picking_ids or (purchase_id and purchase_id.picking_ids):
            if self.picking_ids:
                picking_ids = self.picking_ids.filtered(lambda p: p.state == 'done')
            else:
                picking_ids = purchase_id.picking_ids.filtered(lambda p: p.state == 'done')

            if picking_ids:
                print('picking_ids........', picking_ids[0])
                for line in self.line_ids:
                    if line.account_id == line.product_id.categ_id.property_stock_account_input_categ_id:
                        if self.picking_ids:
                            move = picking_ids[0].move_lines.filtered(lambda x: x.account_move_line_id == line)
                        else:
                            move = picking_ids[0].move_lines.filtered(
                                lambda x: x.purchase_line_id == line.purchase_line_id)
                        move = move.filtered(lambda x: x.state == 'done')
                        print('move', move, move.product_id.name, line.product_id.name)
                        valuation_layer = self.env['stock.valuation.layer'].search([('stock_move_id', '=', move.id)])
                        print('valuation_layer',
                              valuation_layer)
                        valuation_layer.account_move_id.has_reconciled_entries = False
                        to_reconcile = valuation_layer.account_move_id.line_ids.filtered(
                            lambda x: x.account_id == x.product_id.categ_id.property_stock_account_input_categ_id)
                        stj_line = to_reconcile
                        print(to_reconcile, '<<')
                        to_reconcile = to_reconcile + line
                        print('to_reconicile', to_reconcile)
                        stj_line.reconciled = False
                        line.reconciled = False
                        print('reconcile', stj_line, stj_line.reconciled)
                        reconcile = to_reconcile.reconcile()
                        stj_line.move_id.has_reconciled_entries = True
                        print('reconcile-final', reconcile)
        return res

    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        if self.picking_ids:
            context = self.env.context.copy()
            context.update({'cancel_picking': True})
            self.env.context = context
            self.picking_ids.action_cancel()
        return res
