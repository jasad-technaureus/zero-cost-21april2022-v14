# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_repr
import datetime
from datetime import datetime
from collections import defaultdict
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    operation_type = fields.Selection(string='Type of Operation',
                                      selection=[('incoming', 'Receipt'), ('outgoing', 'Delivery'),
                                                 ('internal', 'Internal Transfer'), ('mrp_operation', 'Manufacturing')])
    blank_type = fields.Char(string='Blank Type')
    transfer_id = fields.Many2one('stock.picking', string='Transfer No.')
    order_type = fields.Selection(string='Order Type', selection=[('purchase', 'Purchase'), ('sale', 'Sales')],
                                  default=False)
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order No.')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order No.')
    move_type = fields.Selection(string='Move Type', selection=[
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt')], compute='_compute_move_type')
    is_manual_receipt = fields.Boolean('Is Manual Receipt', related='stock_move_id.is_manual_receipt', store=True)
    state = fields.Selection([('cancel', 'Cancelled'), ('confirm', 'Confirmed')], string='Status', default='confirm')

    team_name = fields.Char(
        string='Sales Team', readonly=True)
    invoice_user_name = fields.Char(copy=False, string='Salesperson', readonly=True)
    unit_cost = fields.Monetary('Unit Cost', readonly=True, group_operator=False)
    margin_per = fields.Float(string='Margin %')
    markup_per = fields.Float(string='Markup %')

    def _compute_move_type(self):
        for val in self:
            val.qty_sold = abs(val.quantity)
            # if val.stock_move_id.picking_id.pos_session_id:
            #     pos_order = self.env['pos.order'].search(
            #         [('session_id', '=', val.stock_move_id.picking_id.pos_session_id.id)])
            #     print('pos_order', pos_order)
            #     val.pos_order_id = pos_order.id
            #     order_line = pos_order.lines.filtered(lambda x: x.product_id == val.product_id)
            #     val.invoiced_unit_price = order_line.price_unit
            #     val.invoiced_amount = val.invoiced_unit_price * abs(val.quantity)

            if val.stock_move_id.picking_id.sale_id:
                val.order_type = 'sale'
                val.sale_order_id = val.stock_move_id.picking_id.sale_id.id
                val.move_type = val.stock_move_id.picking_id.sale_id.invoice_ids[
                    0].move_type if val.stock_move_id.picking_id.sale_id.invoice_ids else False
                val.move_id = val.stock_move_id.picking_id.sale_id.invoice_ids[
                    0].id if val.stock_move_id.picking_id.sale_id.invoice_ids else False
                val.partner_id = val.stock_move_id.picking_id.sale_id.partner_id
                if val.stock_move_id.picking_id.sale_id.invoice_ids:
                    invoice_line = val.stock_move_id.picking_id.sale_id.invoice_ids[0].invoice_line_ids.filtered(
                        lambda x: x.sale_line_ids == val.stock_move_id.sale_line_id)
                    val.invoiced_unit_price = invoice_line.price_unit
                    val.invoiced_amount = val.invoiced_unit_price * abs(val.quantity)
                    val.margin = val.invoiced_amount + val.value
            elif val.stock_move_id.picking_id.purchase_id:
                val.order_type = 'purchase'
                val.purchase_order_id = val.stock_move_id.picking_id.purchase_id.id
                val.move_type = val.stock_move_id.picking_id.purchase_id.invoice_ids[
                    0].move_type if val.stock_move_id.picking_id.purchase_id.invoice_ids else False
                val.move_id = val.stock_move_id.picking_id.purchase_id.invoice_ids[
                    0].id if val.stock_move_id.picking_id.purchase_id.invoice_ids else False
                val.partner_id = val.stock_move_id.picking_id.purchase_id.partner_id
                if val.stock_move_id.picking_id.purchase_id.invoice_ids:
                    invoice_line = val.stock_move_id.picking_id.purchase_id.invoice_ids[0].invoice_line_ids.filtered(
                        lambda x: x.purchase_line_id == val.stock_move_id.purchase_line_id)
                    if invoice_line.currency_id != invoice_line.company_id.currency_id:
                        val.invoiced_unit_price = invoice_line.currency_id._convert(invoice_line.price_unit,
                                                                                    invoice_line.company_id.currency_id,
                                                                                    invoice_line.company_id,
                                                                                    invoice_line.date,
                                                                                    round=True)
                        val.invoiced_amount = val.invoiced_unit_price * val.quantity
                        val.margin = val.invoiced_amount + val.value

                    else:
                        val.invoiced_unit_price = invoice_line.price_unit
                        val.invoiced_amount = val.invoiced_unit_price * val.quantity
                        val.margin = val.invoiced_amount + val.value
            elif val.stock_move_id.picking_id.account_move_id:
                val.move_type = val.stock_move_id.picking_id.account_move_id.move_type
                val.move_id = val.stock_move_id.picking_id.account_move_id.id
                val.partner_id = val.stock_move_id.picking_id.account_move_id.partner_id
                invoice_line = val.stock_move_id.picking_id.account_move_id.invoice_line_ids.filtered(
                    lambda x: x == val.stock_move_id.account_move_line_id)
                val.invoiced_unit_price = invoice_line.price_unit
                val.invoiced_amount = val.invoiced_unit_price * abs(val.quantity)
                val.margin = val.invoiced_amount + val.value
            else:
                val.move_type = False
                val.move_type = False
                val.partner_id = False

            val.team_name = val.stock_move_id.picking_id.account_move_id.team_id.name
            val.invoice_user_name = val.stock_move_id.picking_id.account_move_id.invoice_user_id.name
            val.margin_per = ((
                                      val.invoiced_amount + val.value) / val.invoiced_amount) * 100 if val.invoiced_amount != 0 else 0
            val.markup_per = ((val.invoiced_amount + val.value) / abs(val.value)) * 100 if val.value != 0 else 0

    move_id = fields.Many2one('account.move', string='Move No.')
    partner_id = fields.Many2one('res.partner', string='Partner')
    invoiced_unit_price = fields.Float(string='Unit Price')
    invoiced_amount = fields.Float(string='Total Revenue')
    margin = fields.Float(string='Margin')
    warehouse_name = fields.Char(string='Warehouse')
    location_name = fields.Char(string='Location')
    cost_adjustment_id = fields.Many2one('cost.adjustments', string='Cost Adjustment')
    product_type = fields.Selection(related='product_id.type',
                                    readonly=1)
    qty_sold = fields.Float('Quantity Sold')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(StockValuationLayer, self).create(vals_list)
        print('......................1', res)
        # res.update({
        #     'date_created': datetime.now()
        # })

        for svl in res:
            # if svl.product_id.is_kit:
            #     svl.value =
            if not svl.real_date and svl.stock_move_id:
                svl.real_date = svl.stock_move_id.real_date

            if svl.stock_move_id.picking_id.picking_type_id.code in ['incoming', 'outgoing', 'internal',
                                                                     'mrp_operation']:
                svl.operation_type = svl.stock_move_id.picking_id.picking_type_id.code

                if svl.cost_adjustment_id:
                    svl.blank_type = 'Adjustment'
                    svl.operation_type = False
                if svl.stock_landed_cost_id:
                    svl.blank_type = 'Landed Cost'
                    svl.real_date = svl.stock_landed_cost_id.date
                    svl.operation_type = False
            elif svl.stock_move_id.inventory_id:
                svl.blank_type = 'Inventory Adjustments'
            elif svl.stock_landed_cost_id:
                svl.blank_type = 'Landed Cost'
                svl.real_date = svl.stock_landed_cost_id.date
            elif svl.cost_adjustment_id:
                svl.blank_type = 'Adjustment'
                svl.operation_type = False
            else:
                if not svl.stock_move_id:
                    svl.blank_type = 'Revaluation'
                    svl.real_date = self.env.context.get('real_date')
            svl.transfer_id = svl.stock_move_id.picking_id.id
            svl.warehouse_name = svl.stock_move_id.warehouse_id.name

            if svl.stock_move_id.picking_type_id.code == 'incoming':
                svl.location_name = svl.stock_move_id.picking_id.location_dest_id.complete_name
                print('svl.location_name', svl.location_name)
            elif svl.stock_move_id.picking_type_id.code == 'outgoing':
                svl.location_name = svl.stock_move_id.picking_id.location_id.complete_name
            else:
                print('.......-----', svl.stock_move_id.picking_type_id)
                svl.location_name = svl.stock_move_id.location_id.complete_name
            if svl.real_date:
                real_date = svl.real_date
            else:
                real_date = svl.stock_move_id.real_date
            print('REAL_DATE', real_date, svl.create_date.date())
            if svl.stock_move_id.origin_returned_move_id:
                print('SVL-MAIN', svl)
                return_svl = self.env['stock.valuation.layer'].search(
                    [('stock_move_id', '=', svl.stock_move_id.origin_returned_move_id.id),
                     ('blank_type', '!=', 'Landed Cost')])
                print('return_svl', return_svl)
                # unit_cost = sum(return_svl.mapped('value')) / sum(return_svl.mapped('quantity'))
                # print('unit_cost',unit_cost)
                products = self.env['cost.adjustments'].search(
                    [('product_id', '=', svl.product_id.id)])
                if not products:
                    cost_adjustment = self.env['cost.adjustments'].create(
                        {'product_id': svl.product_id.id})
                    cost_adjustment._compute_count()
                if svl.unit_cost != return_svl.unit_cost:
                    svl.unit_cost = abs(return_svl.unit_cost)
                    svl.value = svl.unit_cost * svl.quantity
                    valuation_layers_all = self.env['stock.valuation.layer'].search(
                        [('product_id', '=', svl.product_id.id), ('real_date', '!=', False),
                         ('move_type', '!=', 'in_invoice'),
                         ('state', '=', 'confirm')])
                    total_quantity = sum(valuation_layers_all.mapped('quantity'))
                    print('hhhhhhhh', total_quantity)
                    value1 = sum(valuation_layers_all.mapped('value'))
                    print('kkkkkkkkkkkkk', value1, total_quantity)
                    svl.product_id.with_context(
                        cost_adjustment=True).standard_price = value1 / total_quantity if total_quantity != 0 else 0
                    return svl
            elif real_date and (
                    real_date < svl.create_date):
                # real_date < svl.date_created):
                if svl.value > 0:
                    out_svl = self.env['stock.valuation.layer'].search(
                        [('value', '<', 0), ('product_id', '=', svl.product_id.id)])
                    to_be_adjusted = out_svl.filtered(
                        lambda x: x.real_date >= svl.real_date)
                    if to_be_adjusted:

                        products = self.env['cost.adjustments'].search(
                            [('product_id', '=', svl.product_id.id)])

                        if not products:
                            cost_adjustment = self.env['cost.adjustments'].create(
                                {'product_id': svl.product_id.id})
                            svl.cost_adjustment_id = cost_adjustment.id
                            cost_adjustment._compute_count()
                    if svl.is_manual_receipt or svl.stock_move_id.inventory_id:
                        svl_layers = self.env['stock.valuation.layer'].search(
                            [('product_id', '=', svl.product_id.id)])
                        to_be_adjusted = svl_layers.filtered(
                            lambda x: x.real_date <= svl.real_date)
                        if to_be_adjusted:
                            products = self.env['cost.adjustments'].search(
                                [('product_id', '=', svl.product_id.id)])
                            if not products:
                                cost_adjustment = self.env['cost.adjustments'].create(
                                    {'product_id': svl.product_id.id})
                                print('cost_adjustment', cost_adjustment.product_id.name)
                                svl.cost_adjustment_id = cost_adjustment.id
                                cost_adjustment._compute_count()

                else:
                    products = self.env['cost.adjustments'].search(
                        [('product_id', '=', svl.stock_move_id.product_id.id)])
                    if not products:
                        cost_adjustment = self.env['cost.adjustments'].create(
                            {'product_id': svl.product_id.id})
                        svl.cost_adjustment_id = cost_adjustment.id
                        cost_adjustment._compute_count()

                        print('svl.cost_adjustment_id', svl.cost_adjustment_id)

            bill_line = svl.stock_move_id.purchase_line_id
            svl._compute_move_type()
            print('??', svl.account_move_id)
            print('bill_line', bill_line)
            if svl.stock_move_id.picking_id.purchase_id.invoice_ids:
                invoice_line = svl.stock_move_id.picking_id.purchase_id.invoice_ids[0].invoice_line_ids.filtered(
                    lambda x: x.purchase_line_id == svl.stock_move_id.purchase_line_id)
                print('invoice_line............:::', invoice_line)
                unit_cost = abs(invoice_line.debit / invoice_line.quantity)
                svl.unit_cost = abs(unit_cost)
                svl.value = svl.unit_cost * svl.quantity
                print('VALUEEE', svl.value)
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _change_standard_price(self, new_price):
        print('new_price-cost', new_price)
        print('new_price-cost', self.env.context)

        """Helper to create the stock valuation layers and the account moves
        after an update of standard price.

        :param new_price: new standard price
        """
        # Handle stock valuation layers.
        if not self.env.context.get('cost_adjustment'):
            if self.filtered(lambda p: p.valuation == 'real_time') and not self.env[
                'stock.valuation.layer'].check_access_rights('read', raise_exception=False):
                raise UserError(
                    _("You cannot update the cost of a product in automated valuation as it leads to the creation of a journal entry, for which you don't have the access rights."))

            svl_vals_list = []
            company_id = self.env.company
            for product in self:
                if product.cost_method not in ('standard', 'average'):
                    continue
                quantity_svl = product.sudo().quantity_svl
                if float_is_zero(quantity_svl, precision_rounding=product.uom_id.rounding):
                    continue
                diff = new_price - product.standard_price
                value = company_id.currency_id.round(quantity_svl * diff)
                if company_id.currency_id.is_zero(value):
                    continue

                svl_vals = {
                    'company_id': company_id.id,
                    'product_id': product.id,
                    'description': _('Product value manually modified (from %s to %s)') % (
                        product.standard_price, new_price),
                    'value': value,
                    'quantity': 0,
                }
                svl_vals_list.append(svl_vals)
            stock_valuation_layers = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)

            # Handle account moves.
            product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}
            am_vals_list = []
            for stock_valuation_layer in stock_valuation_layers:
                product = stock_valuation_layer.product_id
                value = stock_valuation_layer.value

                if product.type != 'product' or product.valuation != 'real_time':
                    continue

                # Sanity check.
                if not product_accounts[product.id].get('expense'):
                    raise UserError(_('You must set a counterpart account on your product category.'))
                if not product_accounts[product.id].get('stock_valuation'):
                    raise UserError(
                        _('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))

                if value < 0:
                    debit_account_id = product_accounts[product.id]['expense'].id
                    credit_account_id = product_accounts[product.id]['stock_valuation'].id
                else:
                    debit_account_id = product_accounts[product.id]['stock_valuation'].id
                    credit_account_id = product_accounts[product.id]['expense'].id

                move_vals = {
                    'journal_id': product_accounts[product.id]['stock_journal'].id,
                    'company_id': company_id.id,
                    'ref': product.default_code,
                    'stock_valuation_layer_ids': [(6, None, [stock_valuation_layer.id])],
                    'move_type': 'entry',
                    'line_ids': [(0, 0, {
                        'name': _(
                            '%(user)s changed cost from %(previous)s to %(new_price)s - %(product)s',
                            user=self.env.user.name,
                            previous=product.standard_price,
                            new_price=new_price,
                            product=product.display_name
                        ),
                        'account_id': debit_account_id,
                        'debit': abs(value),
                        'credit': 0,
                        'product_id': product.id,
                    }), (0, 0, {
                        'name': _(
                            '%(user)s changed cost from %(previous)s to %(new_price)s - %(product)s',
                            user=self.env.user.name,
                            previous=product.standard_price,
                            new_price=new_price,
                            product=product.display_name
                        ),
                        'account_id': credit_account_id,
                        'debit': 0,
                        'credit': abs(value),
                        'product_id': product.id,
                    })],
                }
                am_vals_list.append(move_vals)

            account_moves = self.env['account.move'].sudo().create(am_vals_list)
            if account_moves:
                account_moves._post()

    def _run_fifo_vacuum(self, company=None):
        """Compensate layer valued at an estimated price with the price of future receipts
        if any. If the estimated price is equals to the real price, no layer is created but
        the original layer is marked as compensated.

        :param company: recordset of `res.company` to limit the execution of the vacuum
        """
        # DISABALING ODOO DEFAULT REVALUATON STOCK VALUATION LAYER CREATION
        self.ensure_one()
        if company is None:
            company = self.env.company
        svls_to_vacuum = self.env['stock.valuation.layer'].sudo().search([
            ('product_id', '=', self.id),
            ('remaining_qty', '<', 0),
            ('stock_move_id', '!=', False),
            ('company_id', '=', company.id),
        ], order='create_date, id')
        if not svls_to_vacuum:
            return

        domain = [
            ('company_id', '=', company.id),
            ('product_id', '=', self.id),
            ('remaining_qty', '>', 0),
            ('create_date', '>=', svls_to_vacuum[0].create_date),
        ]
        all_candidates = self.env['stock.valuation.layer'].sudo().search(domain)

        for svl_to_vacuum in svls_to_vacuum:
            # We don't use search to avoid executing _flush_search and to decrease interaction with DB
            candidates = all_candidates.filtered(
                lambda r: r.create_date > svl_to_vacuum.create_date
                          or r.create_date == svl_to_vacuum.create_date
                          and r.id > svl_to_vacuum.id
            )
            if not candidates:
                break
            qty_to_take_on_candidates = abs(svl_to_vacuum.remaining_qty)
            qty_taken_on_candidates = 0
            tmp_value = 0
            for candidate in candidates:
                qty_taken_on_candidate = min(candidate.remaining_qty, qty_to_take_on_candidates)
                qty_taken_on_candidates += qty_taken_on_candidate

                candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                candidate_vals = {
                    'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                    'remaining_value': new_remaining_value
                }
                candidate.write(candidate_vals)
                if not (candidate.remaining_qty > 0):
                    all_candidates -= candidate

                qty_to_take_on_candidates -= qty_taken_on_candidate
                tmp_value += value_taken_on_candidate
                if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                    break

            # Get the estimated value we will correct.
            remaining_value_before_vacuum = svl_to_vacuum.unit_cost * qty_taken_on_candidates
            new_remaining_qty = svl_to_vacuum.remaining_qty + qty_taken_on_candidates
            corrected_value = remaining_value_before_vacuum - tmp_value
            svl_to_vacuum.write({
                'remaining_qty': new_remaining_qty,
            })

            # Don't create a layer or an accounting entry if the corrected value is zero.
            if svl_to_vacuum.currency_id.is_zero(corrected_value):
                continue

            corrected_value = svl_to_vacuum.currency_id.round(corrected_value)
            # move = svl_to_vacuum.stock_move_id
            # vals = {
            #     'product_id': self.id,
            #     'value': corrected_value,
            #     'unit_cost': 0,
            #     'quantity': 0,
            #     'remaining_qty': 0,
            #     'stock_move_id': move.id,
            #     'company_id': move.company_id.id,
            #     'description': 'Revaluation of %s (negative inventory)' % move.picking_id.name or move.name,
            #     'stock_valuation_layer_id': svl_to_vacuum.id,
            # }
            # vacuum_svl = self.env['stock.valuation.layer'].sudo().create(vals)

            # Create the account move.
            if self.valuation != 'real_time':
                continue
            # vacuum_svl.stock_move_id._account_entry_move(
            #     vacuum_svl.quantity, vacuum_svl.description, vacuum_svl.id, vacuum_svl.value
            # )
            # Create the related expense entry
            # self._create_fifo_vacuum_anglo_saxon_expense_entry(vacuum_svl, svl_to_vacuum)

        # If some negative stock were fixed, we need to recompute the standard price.
        product = self.with_company(company.id)
        if product.cost_method == 'average' and not float_is_zero(product.quantity_svl,
                                                                  precision_rounding=self.uom_id.rounding):
            product.sudo().with_context(disable_auto_svl=True).write(
                {'standard_price': product.value_svl / product.quantity_svl})


class StockLandedCost(models.Model):
    _inherit = 'stock.landed.cost'

    def button_validate(self):
        self._check_can_validate()
        cost_without_adjusment_lines = self.filtered(lambda c: not c.valuation_adjustment_lines)
        if cost_without_adjusment_lines:
            cost_without_adjusment_lines.compute_landed_cost()
        if not self._check_sum():
            raise UserError(_('Cost and adjustments lines do not match. You should maybe recompute the landed costs.'))

        for cost in self:
            cost = cost.with_company(cost.company_id)
            move = self.env['account.move']
            move_vals = {
                'journal_id': cost.account_journal_id.id,
                'date': cost.date,
                'ref': cost.name,
                'line_ids': [],
                'move_type': 'entry',
            }
            valuation_layer_ids = []
            cost_to_add_byproduct = defaultdict(lambda: 0.0)
            for line in cost.valuation_adjustment_lines.filtered(lambda line: line.move_id):
                remaining_qty = sum(line.move_id.stock_valuation_layer_ids.mapped('remaining_qty'))
                linked_layer = line.move_id.stock_valuation_layer_ids[:1]

                # Prorate the value at what's still in stock
                cost_to_add = line.additional_landed_cost
                print('cost_to_add', cost_to_add)
                if not cost.company_id.currency_id.is_zero(cost_to_add):
                    valuation_layer = self.env['stock.valuation.layer'].create({
                        'value': cost_to_add,
                        'unit_cost': 0,
                        'quantity': 0,
                        'remaining_qty': 0,
                        'stock_valuation_layer_id': linked_layer.id,
                        'description': cost.name,
                        'stock_move_id': line.move_id.id,
                        'product_id': line.move_id.product_id.id,
                        'stock_landed_cost_id': cost.id,
                        'company_id': cost.company_id.id,
                    })
                    linked_layer.remaining_value += cost_to_add
                    valuation_layer_ids.append(valuation_layer.id)
                    print('valuation_layer-landed', valuation_layer)
                # Update the AVCO
                product = line.move_id.product_id
                if product.cost_method == 'average':
                    cost_to_add_byproduct[product] += cost_to_add
                # `remaining_qty` is negative if the move is out and delivered proudcts that were not
                # in stock.
                qty_out = 0
                if line.move_id._is_in():
                    qty_out = line.move_id.product_qty - remaining_qty
                elif line.move_id._is_out():
                    qty_out = line.move_id.product_qty
                move_vals['line_ids'] += line._create_accounting_entries(move, qty_out)

            # batch standard price computation avoid recompute quantity_svl at each iteration
            products = self.env['product.product'].browse(p.id for p in cost_to_add_byproduct.keys())
            for product in products:  # iterate on recordset to prefetch efficiently quantity_svl
                if not float_is_zero(product.quantity_svl, precision_rounding=product.uom_id.rounding):
                    product.with_company(cost.company_id).sudo().with_context(disable_auto_svl=True).standard_price += \
                        cost_to_add_byproduct[product] / product.quantity_svl

            move_vals['stock_valuation_layer_ids'] = [(6, None, valuation_layer_ids)]
            move = move.create(move_vals)
            cost.write({'state': 'done', 'account_move_id': move.id})
            move._post()

            if cost.vendor_bill_id and cost.vendor_bill_id.state == 'posted' and cost.company_id.anglo_saxon_accounting:
                all_amls = cost.vendor_bill_id.line_ids | cost.account_move_id.line_ids
                for product in cost.cost_lines.product_id:
                    accounts = product.product_tmpl_id.get_product_accounts()
                    input_account = accounts['stock_input']
                    all_amls.filtered(
                        lambda aml: aml.account_id == input_account and not aml.full_reconcile_id).reconcile()

        return True

    def button_cancel(self):
        # if any(cost.state == 'done' for cost in self):
        #     raise UserError(
        #         _('Validated landed costs cannot be cancelled, but you could create negative landed costs to reverse them'))
        svls = self.env['stock.valuation.layer'].search([('stock_landed_cost_id', '=', self.id)])

        self.account_move_id.button_draft()
        self.account_move_id.button_cancel()
        for svl in svls:
            svl.state = 'cancel'
            products = self.env['cost.adjustments'].search([('product_id', '=', svl.product_id.id)])
            if not products:
                cost_adjustment = self.env['cost.adjustments'].create(
                    {'product_id': svl.product_id.id})
                cost_adjustment._compute_count()
        return self.write({'state': 'cancel'})


class AdjustmentLines(models.Model):
    _inherit = 'stock.valuation.adjustment.lines'

    def _create_account_move_line(self, move, credit_account_id, debit_account_id, qty_out, already_out_account_id):
        print('debit_account_id', debit_account_id)
        """
        Generate the account.move.line values to track the landed cost.
        Afterwards, for the goods that are already out of stock, we should create the out moves
        """
        AccountMoveLine = []

        base_line = {
            'name': self.name,
            'product_id': self.product_id.id,
            'quantity': 0,
        }
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_landed_cost
        if diff > 0:
            debit_line['debit'] = diff
            credit_line['credit'] = diff
        else:
            # negative cost, reverse the entry
            debit_line['credit'] = -diff
            credit_line['debit'] = -diff
        AccountMoveLine.append([0, 0, debit_line])
        AccountMoveLine.append([0, 0, credit_line])

        # Create account move lines for quants already out of stock
        # Disabled Account move lines for quants already out of stock As per Requirement
        # if qty_out > 0:
        #     debit_line = dict(base_line,
        #                       name=(self.name + ": " + str(qty_out) + _(' already out')),
        #                       quantity=0,
        #                       account_id=already_out_account_id)
        #     credit_line = dict(base_line,
        #                        name=(self.name + ": " + str(qty_out) + _(' already out')),
        #                        quantity=0,
        #                        account_id=debit_account_id)
        #     diff = diff * qty_out / self.quantity
        #     if diff > 0:
        #         debit_line['debit'] = diff
        #         credit_line['credit'] = diff
        #     else:
        #         # negative cost, reverse the entry
        #         debit_line['credit'] = -diff
        #         credit_line['debit'] = -diff
        #     AccountMoveLine.append([0, 0, debit_line])
        #     AccountMoveLine.append([0, 0, credit_line])

        # if self.env.company.anglo_saxon_accounting:
        #     expense_account_id = self.product_id.product_tmpl_id.get_product_accounts()['expense'].id
        #     debit_line = dict(base_line,
        #                       name=(self.name + ": " + str(qty_out) + _(' already out')),
        #                       quantity=0,
        #                       account_id=expense_account_id)
        #     credit_line = dict(base_line,
        #                        name=(self.name + ": " + str(qty_out) + _(' already out')),
        #                        quantity=0,
        #                        account_id=already_out_account_id)
        #
        #     if diff > 0:
        #         debit_line['debit'] = diff
        #         credit_line['credit'] = diff
        #     else:
        #         # negative cost, reverse the entry
        #         debit_line['credit'] = -diff
        #         credit_line['debit'] = -diff
        #     AccountMoveLine.append([0, 0, debit_line])
        #     AccountMoveLine.append([0, 0, credit_line])

        return AccountMoveLine


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        print('self.....', self.picking_type_id.code)
        if self.picking_type_id.code == 'incoming':
            if self.purchase_id and self.purchase_id.invoice_ids:
                bill = self.purchase_id.invoice_ids.filtered(lambda x: x.state != 'cancel')
                if self.purchase_id.currency_id != self.purchase_id.company_id.currency_id:
                    if bill.currency_id != bill.company_id.currency_id:
                        # purchase_rate = 1 / self.purchase_id.currency_rate
                        purchase_rate = self.purchase_id.currency_id.rate
                        bill_rate = bill.main_curr_rate
                        bill_rate = 1 / bill_rate
                        print('RATE..........', round(purchase_rate, 5), round(bill_rate, 5))
                        if round(purchase_rate, 5) != round(bill_rate, 5):
                            print('Different Bill Rate')
                            # bill_product_ids = bill.invoice_line_ids.mapped('product_id').ids
                            # products = self.env['cost.adjustments'].search(
                            #     [('product_id', 'in', bill_product_ids)])
                            for line in bill.line_ids:
                                move = self.move_lines.filtered(
                                    lambda x: x.purchase_line_id == line.purchase_line_id)
                                if move:
                                    valuation_layer = self.env['stock.valuation.layer'].search(
                                        [('stock_move_id', '=', move.id), ('state', '=', 'confirm'),
                                         ('blank_type', '!=', 'Landed Cost')])
                                    print('valuation_layer_check', valuation_layer)
                                    print('line.....', line.debit)
                                    print('-----', valuation_layer.unit_cost, valuation_layer.invoiced_unit_price)
                                    if valuation_layer:
                                        if valuation_layer.stock_move_id.picking_id.purchase_id.invoice_ids:
                                            invoice_line = valuation_layer.stock_move_id.picking_id.purchase_id.invoice_ids[
                                                0].invoice_line_ids.filtered(
                                                lambda x: x.purchase_line_id == valuation_layer.stock_move_id.purchase_line_id)
                                            print('invoice_line............:::', invoice_line)
                                            unit_cost = abs(invoice_line.debit / invoice_line.quantity)
                                            valuation_layer.unit_cost = abs(unit_cost)
                                            valuation_layer.value = valuation_layer.unit_cost * valuation_layer.quantity
                                            print('VALUEEE2', valuation_layer.value)
                                        # if valuation_layer.unit_cost != valuation_layer.invoiced_unit_price:
                                        #     valuation_layer.value = line.debit
                                        #     valuation_layer.unit_cost = valuation_layer.value / valuation_layer.quantity
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
                                            valuation_layer.unit_cost = abs(valuation_layer.value / valuation_layer.quantity)
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
                            print('Same Bill Rate')
                            for line in bill.line_ids:
                                move = self.move_lines.filtered(
                                    lambda x: x.purchase_line_id == line.purchase_line_id)
                                if move:
                                    valuation_layer = self.env['stock.valuation.layer'].search(
                                        [('stock_move_id', '=', move.id), ('state', '=', 'confirm'),
                                         ('blank_type', '!=', 'Landed Cost')])
                                    print('line.....fff', line.debit)
                                    valuation_layer.value = line.debit
                                    valuation_layer.unit_cost = abs(valuation_layer.value / valuation_layer.quantity) if valuation_layer.quantity!=0 else 0
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

                purchase_id = self.purchase_id
                if purchase_id.currency_id != bill.currency_id:
                    for line in bill.line_ids:
                        move = self.move_lines.filtered(
                            lambda x: x.purchase_line_id == line.purchase_line_id)
                        print('move...', move)
                        if move:
                            valuation_layer = self.env['stock.valuation.layer'].search(
                                [('stock_move_id', '=', move.id), ('state', '=', 'confirm'),
                                 ('blank_type', '!=', 'Landed Cost')])
                            print('valuation_layer%', valuation_layer)
                            print('line.....', line.debit)
                            if valuation_layer:
                                valuation_layer.value = line.debit
                                valuation_layer.unit_cost = abs(valuation_layer.value / valuation_layer.quantity)
                                valuation_layer.account_move_id.button_draft()
                                credit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.credit > 0)
                                credit_line.with_context(check_move_validity=False).credit = abs(valuation_layer.value)
                                debit_line = valuation_layer.account_move_id.line_ids.filtered(lambda x: x.debit > 0)
                                debit_line.with_context(check_move_validity=False).debit = abs(valuation_layer.value)
                                valuation_layer.account_move_id.action_post()

                for line in bill.invoice_line_ids:
                    purchase_line = line.purchase_line_id.order_id.order_line.filtered(
                        lambda x: x == line.purchase_line_id)

                    if purchase_line and purchase_line.price_unit != line.price_unit:
                        products = self.env['cost.adjustments'].search([('product_id', '=', line.product_id.id)])
                        print('products', products)
                        if not products:
                            cost_adjustment = self.env['cost.adjustments'].create({'product_id': line.product_id.id,
                                                                                   'is_from_bll': True})
                            cost_adjustment.ca_adjust_confirm()
                            cost_adjustment._compute_count()
                        else:
                            products.ca_adjust_confirm()

                for line in bill.line_ids:
                    if line.account_id == line.product_id.categ_id.property_stock_account_input_categ_id:
                        move = self.move_lines.filtered(lambda x: x.purchase_line_id == line.purchase_line_id)
                        print('move', move, move.product_id.name, line.product_id.name)
                        valuation_layer = self.env['stock.valuation.layer'].search(
                            [('stock_move_id', '=', move.id), ('state', '=', 'confirm'),
                             ('blank_type', '!=', 'Landed Cost')])
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

    def action_cancel(self):
        for picking in self:
            if picking.state == 'done':
                context = self.env.context.copy()
                context.update({'cancel_picking': True})
                self.env.context = context
            picking.mapped('move_lines')._action_cancel()
            picking.write({'is_locked': True})
        return True


class StockMove(models.Model):
    _inherit = 'stock.move'
    is_manual_receipt = fields.Boolean('Is Manual Receipt', default=False)

    def create(self, vals_list):
        res = super(StockMove, self).create(vals_list)
        if res.picking_id:
            if res.picking_id.picking_type_id.code == 'incoming' and not res.picking_id.purchase_id and not res.picking_id.account_move_id and not res.origin_returned_move_id:
                res.is_manual_receipt = True
        return res

    def _action_cancel(self):
        print('ids........', self.ids)
        if not self.env.context.get('cancel_picking'):
            if any(move.state == 'done' and not move.scrapped for move in self):
                raise UserError(
                    _('You cannot cancel a stock move that has been set to \'Done\'. Create a return in order to reverse the moves which took place.'))
            moves_to_cancel = self.filtered(lambda m: m.state != 'cancel')
        else:
            moves_to_cancel = self.filtered(lambda m: m.state != 'cancel')
            moves_to_cancel.state = 'cancel'
            valuation_layers_to_cancel = self.env['stock.valuation.layer'].search([('stock_move_id', 'in', self.ids)])
            print('valuation_layers_to_cancel', valuation_layers_to_cancel)
            valuation_layers_to_cancel.state = 'cancel'
            for layer in valuation_layers_to_cancel:
                products = self.env['cost.adjustments'].search(
                    [('product_id', '=', layer.product_id.id)])
                if not products:
                    cost_adjustment = self.env['cost.adjustments'].create(
                        {'product_id': layer.product_id.id})
                    cost_adjustment._compute_count()
                if layer.account_move_id:
                    layer.account_move_id.button_draft()
                    layer.account_move_id.button_cancel()

        # self cannot contain moves that are either cancelled or done, therefore we can safely
        # unlink all associated move_line_ids
        moves_to_cancel._do_unreserve()

        for move in moves_to_cancel:
            siblings_states = (move.move_dest_ids.mapped('move_orig_ids') - move).mapped('state')
            in_quant = self.env['stock.quant'].search(
                [('location_id', '=', move.location_dest_id.id), ('product_id', '=', move.product_id.id)])
            print('in_quant.....', in_quant, in_quant.sudo().quantity)
            out_quant = self.env['stock.quant'].search(
                [('location_id', '=', move.location_id.id), ('product_id', '=', move.product_id.id)])
            print('out_quants.....2', out_quant, out_quant.sudo().quantity)
            # if move.state == 'done':
            print('QTY......', move, move.product_uom_qty)
            print('QTY......2', in_quant.sudo().quantity)
            print('QTY......5', move._is_in(), move._is_out())
            if move._is_in() and move:
                print('In..........', )
                in_quant.sudo().quantity -= move.product_uom_qty
                out_quant.sudo().quantity += move.product_uom_qty
                print('quant.................', out_quant.sudo().quantity, in_quant.sudo().quantity, )
            elif move._is_out():
                print('OUT..........')
                out_quant.sudo().quantity += move.product_uom_qty
                in_quant.sudo().quantity -= move.product_uom_qty
            if move.propagate_cancel:
                # only cancel the next move if all my siblings are also cancelled
                if all(state == 'cancel' for state in siblings_states):
                    move.move_dest_ids.filtered(lambda m: m.state != 'done')._action_cancel()
            else:
                if all(state in ('done', 'cancel') for state in siblings_states):
                    move.move_dest_ids.write({'procure_method': 'make_to_stock'})
                    move.move_dest_ids.write({'move_orig_ids': [(3, move.id, 0)]})
        self.write({
            'state': 'cancel',
            'move_orig_ids': [(5, 0, 0)],
            'procure_method': 'make_to_stock',
        })
        return True


class StockInventory(models.Model):
    _inherit = 'stock.inventory'
    accounting_date = fields.Date(
        'Accounting Date',
        help="Date at which the accounting entries will be created"
             " in case of automated inventory valuation."
             " If empty, the inventory date will be used.", default=fields.Date.context_today, required=True)

    def action_cancel_adjustment(self):
        context = self.env.context.copy()
        context.update({'cancel_picking': True})
        self.env.context = context
        self.move_ids._action_cancel()
        self.state = 'cancel'
