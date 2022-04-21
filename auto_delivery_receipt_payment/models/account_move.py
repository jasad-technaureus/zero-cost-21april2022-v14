# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, get_lang
from odoo.tools.safe_eval import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'

    auto_inventory = fields.Boolean(string="Auto Delivery/Auto Receipt")
    auto_payment = fields.Boolean(string="Auto Payment")
    operation_type_id = fields.Many2one('stock.picking.type', string="Operation Type")
    payment_journal_id = fields.Many2one('account.journal', string='Payment Journal')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    is_from_po_or_so = fields.Boolean(string="Flag to know whether bill/invoice from sale/purchase")
    picking_ids = fields.One2many('stock.picking', 'account_move_id', compute='_compute_picking', string='Receptions',
                                  copy=False,
                                  store=True)
    picking_count = fields.Integer(compute='_compute_picking', string='Picking count', default=0, store=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    show_update_pricelist = fields.Boolean(string='Has Pricelist Changed',
                                           help="Technical Field, True if the pricelist was changed;\n"
                                                " this will then display a recomputation button")

    @api.onchange('pricelist_id', 'invoice_line_ids')
    def _onchange_pricelist_id(self):
        if self.invoice_line_ids and self.pricelist_id and self._origin.pricelist_id != self.pricelist_id:
            self.show_update_pricelist = True
        else:
            self.show_update_pricelist = False

    def update_prices(self):
        self.ensure_one()
        lines_to_update = []
        for line in self.invoice_line_ids:
            product = line.product_id.with_context(
                partner=self.partner_id,
                quantity=line.quantity,
                date=self.date,
                pricelist=self.pricelist_id.id,
                uom=line.product_uom_id.id
            )
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                line._get_display_price(product), line.product_id.taxes_id, line.tax_ids, line.company_id)
            if self.pricelist_id.discount_policy == 'without_discount' and price_unit:
                discount = max(0, (price_unit - product.price) * 100 / price_unit)
            else:
                discount = 0
            lines_to_update.append((1, line.id, {'price_unit': price_unit, 'discount': discount}))
        self.update({'invoice_line_ids': lines_to_update})
        self.show_update_pricelist = False
        self.message_post(body=_("Product prices have been recomputed according to pricelist <b>%s<b> ",
                                 self.pricelist_id.display_name))

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        if self.pricelist_id:
            if self.pricelist_id.currency_id != self.currency_id:
                self.currency_id = self.pricelist_id.currency_id.id
                for line in self.invoice_line_ids:
                    line.currency_id = self.currency_id

    @api.depends('picking_ids')
    def _compute_picking(self):
        for order in self:
            # pick_ids = self.env['stock.picking'].search(
            #     [('partner_id', '=', order.partner_id.id), ('origin', '=', order.name),
            #      ('picking_type_id', '=', order.operation_type_id.id)])
            # print("pick_ids", pick_ids)
            order.picking_count = len(order.picking_ids)
            # [[4, tax_template_ref[tax.id], 0] for tax in line.tax_ids],

    @api.onchange('partner_id')
    def onchange_customer_auto(self):
        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist
            if self.invoice_line_ids and self.pricelist_id and self._origin.pricelist_id != self.pricelist_id:
                self.show_update_pricelist = True
            else:
                self.show_update_pricelist = False

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.move_type in ['out_invoice', 'in_invoice']:
            if self.journal_id.auto_payment and not self.is_from_po_or_so:
                self.auto_payment = True
                self.payment_journal_id = self.journal_id.payment_journal_id
            else:
                self.auto_payment = False
                self.payment_journal_id = False
            if self.journal_id.auto_inventory and not self.is_from_po_or_so:
                self.auto_inventory = True
                self.warehouse_id = self.journal_id.warehouse_id if self.move_type == 'out_invoice' else None
                self.operation_type_id = self.journal_id.operation_type_id if self.move_type == 'in_invoice' else None
            else:
                self.auto_inventory = False
                self.operation_type_id = False
        else:
            self.auto_inventory = False
            self.operation_type_id = False
            self.payment_journal_id = False

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.move_type in ['out_invoice', 'in_invoice']:
            if self.auto_payment and self.payment_journal_id:
                partner_type = ''
                amount = 0.0
                payment_type = ''
                if self.move_type == 'in_invoice':
                    partner_type = 'supplier'
                    payment_type = 'outbound'
                elif self.move_type == 'out_invoice':
                    partner_type = 'customer'
                    payment_type = 'inbound'
                if self.currency_id != self.company_id.currency_id:
                    if self.payment_journal_id.currency_id == self.company_id.currency_id:
                        amount = abs(self.amount_total_signed)
                    elif self.payment_journal_id.currency_id != self.currency_id:
                        if self.payment_journal_id.currency_id:
                            amount = abs(self.amount_total_signed) * self.payment_journal_id.currency_id.rate
                        else:
                            raise UserError(_('Please Set a Currency in Payment Journal'))
                        print(amount, (self.amount_total_signed),
                              self.payment_journal_id.currency_id.rate,
                              2)
                    elif self.payment_journal_id.currency_id == self.currency_id:
                        amount = self.amount_total
                        print('self.amount_total', self.amount_total)
                    else:
                        amount = abs(self.amount_total_signed)
                elif self.currency_id == self.company_id.currency_id:
                    if self.payment_journal_id.currency_id == self.company_id.currency_id:
                        amount = self.amount_total
                    elif self.payment_journal_id.currency_id != self.company_id.currency_id:
                        amount = self.amount_total * self.main_curr_rate
                    else:
                        amount = self.amount_total

                to_reconcile = []
                print('amount....', amount)
                payments = self.env['account.payment'].create(
                    {'payment_type': payment_type, 'partner_type': partner_type,
                     'partner_id': self.partner_id.id, 'date': self.date,
                     'journal_id': self.payment_journal_id.id, 'amount': amount,
                     'ref': self.name})
                # payment.action_post()
                # self.payment_state = 'paid'
                #
                if self.move_type == 'out_invoice':
                    account_id = self.partner_id.property_account_receivable_id
                elif self.move_type == 'in_invoice':
                    account_id = self.partner_id.property_account_payable_id

                line = self.line_ids.filtered(
                    lambda l: l.account_id == account_id)
                to_reconcile.append(line)
                #     line.reconcile()
                # self.payment_state = 'in_payment'
                for payment, lines in zip(payments, to_reconcile):
                    # Batches are made using the same currency so making 'lines.currency_id' is ok.
                    if payment.currency_id != lines.currency_id:
                        liquidity_lines, counterpart_lines, writeoff_lines = payment._seek_for_lines()
                        source_balance = abs(sum(lines.mapped('amount_residual')))
                        print('source_balance......', liquidity_lines.name, liquidity_lines[0].amount_currency,
                              liquidity_lines[0].balance)
                        payment_rate = liquidity_lines[0].amount_currency / liquidity_lines[0].balance if \
                            liquidity_lines[0].balance else 0
                        source_balance_converted = abs(source_balance) * payment_rate

                        # Translate the balance into the payment currency is order to be able to compare them.
                        # In case in both have the same value (12.15 * 0.01 ~= 0.12 in our example), it means the user
                        # attempt to fully paid the source lines and then, we need to manually fix them to get a perfect
                        # match.
                        payment_balance = abs(sum(counterpart_lines.mapped('balance')))
                        payment_amount_currency = abs(sum(counterpart_lines.mapped('amount_currency')))
                        if not payment.currency_id.is_zero(source_balance_converted - payment_amount_currency):
                            continue

                        delta_balance = source_balance - payment_balance

                        # Balance are already the same.
                        if self.company_currency_id.is_zero(delta_balance):
                            continue

                        # Fix the balance but make sure to peek the liquidity and counterpart lines first.
                        debit_lines = (liquidity_lines + counterpart_lines).filtered('debit')
                        credit_lines = (liquidity_lines + counterpart_lines).filtered('credit')
                        if debit_lines:
                            payment.move_id.write({'line_ids': [
                                (1, debit_lines[0].id, {'debit': debit_lines[0].debit + delta_balance}),
                                (1, credit_lines[0].id, {'credit': credit_lines[0].credit + delta_balance}),
                            ]})

                payments.action_post()

                domain = [('account_internal_type', 'in', ('receivable', 'payable')), ('reconciled', '=', False)]
                for payment, lines in zip(payments, to_reconcile):

                    # When using the payment tokens, the payment could not be posted at this point (e.g. the transaction failed)
                    # and then, we can't perform the reconciliation.
                    if payment.state != 'posted':
                        continue

                    payment_lines = payment.line_ids.filtered_domain(domain)
                    print('payment_lines.....', payment_lines)
                    for account in payment_lines.account_id:
                        print('reconcile....', (payment_lines + lines) \
                              .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]))
                        (payment_lines + lines) \
                            .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                            .reconcile()
            if self.auto_inventory and (self.operation_type_id or self.warehouse_id):
                location_id = ''
                dest_location_id = ''
                if self.operation_type_id:
                    if self.partner_id.property_stock_supplier.id:
                        location_id = self.partner_id.property_stock_supplier.id
                    else:
                        location_id = self.operation_type_id.default_location_src_id.id
                elif self.warehouse_id:
                    if self.warehouse_id.lot_stock_id:
                        location_id = self.warehouse_id.lot_stock_id.id
                    else:
                        location_id = self.warehouse_id.out_type_id.default_location_src_id.id
                    if self.partner_id.property_stock_customer.id:
                        dest_location_id = self.partner_id.property_stock_customer.id
                    else:
                        dest_location_id = self.warehouse_id.out_type_id.default_location_dest_id.id
                import pytz
                from datetime import datetime
                from datetime import timedelta
                local = pytz.timezone(self.env.user.tz)
                naive_start = datetime.strptime(str(self.invoice_date), "%Y-%m-%d")
                local_dt_start = local.localize(naive_start, is_dst=None)
                utc_dt_start = local_dt_start.astimezone(pytz.utc)
                utc_dt_start = utc_dt_start + timedelta(hours=6)
                print('utc_dt_start1', utc_dt_start, type(utc_dt_start))
                utc_dt_start = utc_dt_start.strftime("%Y-%m-%d %H:%M:%S")
                print('utc_dt_start', utc_dt_start, type(utc_dt_start))
                picking = self.env['stock.picking'].create(
                    {'partner_id': self.partner_id.id,
                     'picking_type_id': self.operation_type_id.id if self.operation_type_id else self.warehouse_id.out_type_id.id,
                     'real_date': utc_dt_start,
                     'real_date_display': utc_dt_start,
                     'origin': self.name, 'move_type': 'direct',
                     'location_id': location_id,
                     'location_dest_id': self.operation_type_id.default_location_dest_id.id if self.operation_type_id else dest_location_id,
                     'account_move_id': self.id,
                     })
                print('picking-1', picking, picking.real_date)
                self.write({'picking_ids': [(4, picking.id)]})
                for line in self.invoice_line_ids:
                    price_unit = line.price_subtotal / line.quantity
                    if self.currency_id != self.company_id.currency_id:
                        price_unit = (line.price_subtotal / line.quantity) * self.main_curr_rate
                    # if line.product_id.bom_ids and line.product_id.bom_ids.filtered(
                    #         lambda x: x.type == 'phantom') and self.move_type == 'out_invoice':
                    #     boms = line.product_id.bom_ids.filtered(lambda x: x.type == 'phantom')
                    #     if boms:
                    #         for component in boms[0].bom_line_ids:
                    #             if component.product_id.type != 'service':
                    #                 new_move = self.env['stock.move'].with_context(auto_receipt=True).create(
                    #                     {'product_id': component.product_id.id, 'price_unit': price_unit,
                    #                      'name': component.product_id.name,
                    #                      'product_uom': component.product_uom_id.id,
                    #                      'product_uom_qty': component.product_qty * line.quantity,
                    #                      'forecast_availability': component.product_qty * line.quantity,
                    #                      'quantity_done': component.product_qty * line.quantity,
                    #                      'picking_id': picking.id,
                    #                      'location_id': picking.location_id.id,
                    #                      'location_dest_id': picking.location_dest_id.id,
                    #                      'real_date': self.date,
                    #                      })
                    # if line.product_id.is_kit and self.move_type == 'out_invoice':
                    #     if line.product_id.product_kit_ids:
                    #         for component in line.product_id.product_kit_ids:
                    #             if component.component_id.type != 'service':
                    #                 new_move = self.env['stock.move'].with_context(auto_receipt=True).create(
                    #                     {'product_id': component.component_id.id, 'price_unit': price_unit,
                    #                      'name': component.component_id.name,
                    #                      'product_uom': component.uom_id.id,
                    #                      'product_uom_qty': component.qty * line.quantity,
                    #                      'forecast_availability': component.qty * line.quantity,
                    #                      'quantity_done': component.qty * line.quantity,
                    #                      'picking_id': picking.id,
                    #                      'location_id': picking.location_id.id,
                    #                      'location_dest_id': picking.location_dest_id.id,
                    #                      'real_date': self.date,
                    #                      })
                    # new_move.state = 'done'
                    if line.product_id:
                        if line.product_id.type != 'service':
                            new_move = self.env['stock.move'].with_context(auto_receipt=True).create(
                                {'product_id': line.product_id.id, 'price_unit': price_unit, 'name': line.name,
                                 'product_uom': line.product_uom_id.id,
                                 'product_uom_qty': line.quantity,
                                 'forecast_availability': line.quantity,
                                 'quantity_done': line.quantity,
                                 'picking_id': picking.id,
                                 'location_id': picking.location_id.id,
                                 'location_dest_id': picking.location_dest_id.id,
                                 'picking_type_id': picking.picking_type_id.id,
                                 'real_date': self.date,
                                 'account_move_line_id': line.id,
                                 'warehouse_id': picking.picking_type_id.warehouse_id.id,

                                 })

                if self.move_type == 'out_invoice':
                    quant_dict = {}
                    for move in picking.move_ids_without_package:
                        if move.product_id.type == 'product':
                            quant = move.env['stock.quant'].search(
                                [('product_id', '=', move.product_id.id), ('location_id', '=', picking.location_id.id)])
                            if quant:
                                if quant.available_quantity < move.product_uom_qty:
                                    if move.product_id.default_code:
                                        product = move.product_id.default_code + ' - ' + move.product_id.name
                                    else:
                                        product = move.product_id.name
                                    quant_dict[
                                        product] = quant.available_quantity
                            else:
                                if move.product_id.default_code:
                                    product = move.product_id.default_code + ' - ' + move.product_id.name
                                else:
                                    product = move.product_id.name
                                quant_dict[
                                    product] = 0.0
                    if quant_dict:
                        info = ''
                        for product, availibility in quant_dict.items():
                            info = info + product + ' - Available Qty' + ' = ' + str(availibility) + '\n' + ' '

                        raise UserError(_('The following products do not have enough available quantity:\n %s') % info)
                context = self.env.context.copy()
                context.update({'picking_ids_not_to_backorder': picking.id, 'auto_receipt_kit': True})
                self.env.context = context
                if picking.move_ids_without_package:
                    picking.with_context(auto_receipt=True, account_move=self).button_validate()
                else:
                    picking.unlink()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('invoice_origin'):
                self.is_from_po_or_so = True
                self.auto_inventory = False
                val['is_from_po_or_so'] = True
            if val.get('auto_inventory'):
                if val.get('move_type') and val.get('move_type') not in ['in_invoice', 'out_invoice']:
                    val['auto_inventory'] = False
        return super(AccountMove, self).create(vals_list)

    def action_view_picking(self):
        pickings = self.mapped('picking_ids')
        result = self.env["ir.actions.actions"]._for_xml_id('stock.action_picking_tree_all')
        if len(pickings) > 1:
            # override the context to get rid of the default filtering on operation type
            result['context'] = {'default_partner_id': self.partner_id.id, 'default_origin': self.name,
                                 'default_picking_type_id': self.operation_type_id.id, 'real_date': self.date,
                                 'account_move_id': self.id}

            result['domain'] = "[('id','in',%s)]" % (self.picking_ids.ids)
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pickings.id

        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.onchange('product_uom_id', 'quantity')
    def product_uom_change(self):
        if not self.product_uom_id or not self.product_id:
            self.price_unit = 0.0
            return
        if self.move_id.pricelist_id and self.move_id.partner_id:
            product = self.product_id.with_context(
                lang=self.move_id.partner_id.lang,
                partner=self.move_id.partner_id,
                quantity=self.quantity,
                date=self.move_id.date,
                pricelist=self.move_id.pricelist_id.id,
                uom=self.product_uom_id.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_ids,
                                                                                      self.company_id)

    def _get_display_price(self, product):

        # TO DO: move me in master/saas-16 on sale.order
        # awa: don't know if it's still the case since we need the "product_no_variant_attribute_value_ids" field now
        # to be able to compute the full price

        # it is possible that a no_variant attribute is still in a variant if
        # the type of the attribute has been changed after creation.
        # no_variant_attributes_price_extra = [
        #     ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
        #         lambda ptav:
        #         ptav.price_extra and
        #         ptav not in product.product_template_attribute_value_ids
        #     )
        # ]
        # if no_variant_attributes_price_extra:
        #     product = product.with_context(
        #         no_variant_attributes_price_extra=tuple(no_variant_attributes_price_extra)
        #     )

        if self.move_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.move_id.pricelist_id.id, uom=self.product_uom_id.id).price
        product_context = dict(self.env.context, partner_id=self.move_id.partner_id.id, date=self.move_id.date,
                               uom=self.product_uom_id.id)

        final_price, rule_id = self.move_id.pricelist_id.with_context(product_context).get_product_price_rule(
            product or self.product_id, self.quantity or 1.0, self.move_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           self.quantity,
                                                                                           self.product_uom_id,
                                                                                           self.move_id.pricelist_id.id)
        if currency != self.move_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price, self.move_id.pricelist_id.currency_id,
                self.move_id.company_id or self.env.company, self.move_id.date or fields.Date.today())

        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
            :param obj product: object of current product record
            :parem float qty: total quentity of product
            :param tuple price_and_rule: tuple(price, suitable_rule) coming from pricelist computation
            :param obj uom: unit of measure of current order line
            :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env['product.pricelist.item']
        field_name = 'lst_price'
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == 'without_discount':
                while pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id and pricelist_item.base_pricelist_id.discount_policy == 'without_discount':
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(uom=uom.id).get_product_price_rule(
                        product, qty, self.move_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == 'standard_price':
                field_name = 'standard_price'
                product_currency = product.cost_currency_id
            elif pricelist_item.base == 'pricelist' and pricelist_item.base_pricelist_id:
                field_name = 'price'
                product = product.with_context(pricelist=pricelist_item.base_pricelist_id.id)
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(product_currency, currency_id,
                                                              self.company_id or self.env.company,
                                                              self.order_id.date_order or fields.Date.today())

        product_uom = self.env.context.get('uom') or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0
        return product[field_name] * uom_factor * cur_factor, currency_id

    @api.onchange('product_id', 'price_unit', 'product_uom_id', 'quantity', 'tax_ids')
    def _onchange_discount_pricelist(self):
        if not (self.product_id and self.product_uom_id and
                self.move_id.partner_id and self.move_id.pricelist_id and
                self.move_id.pricelist_id.discount_policy == 'without_discount' and
                self.env.user.has_group('product.group_discount_per_so_line')):
            return

        self.discount = 0.0
        product = self.product_id.with_context(
            lang=self.move_id.partner_id.lang,
            partner=self.move_id.partner_id,
            quantity=self.quantity,
            date=self.move_id.date,
            pricelist=self.move_id.pricelist_id.id,
            uom=self.product_uom_id.id,
            fiscal_position=self.env.context.get('fiscal_position')
        )

        product_context = dict(self.env.context, partner_id=self.move_id.partner_id.id, date=self.move_id.date,
                               uom=self.product_uom_id.id)

        price, rule_id = self.move_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.quantity or 1.0, self.move_id.partner_id)
        new_list_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                               self.quantity,
                                                                                               self.product_uom_id,
                                                                                               self.move_id.pricelist_id.id)

        if new_list_price != 0:
            if self.move_id.pricelist_id.currency_id != currency:
                # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                new_list_price = currency._convert(
                    new_list_price, self.move_id.pricelist_id.currency_id,
                    self.move_id.company_id or self.env.company, self.move_id.date or fields.Date.today())
            discount = (new_list_price - price) / new_list_price * 100
            if (discount > 0 and new_list_price > 0) or (discount < 0 and new_list_price < 0):
                self.discount = discount

    @api.onchange('product_id')
    def product_id_change_auto(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        # for pacv in self.product_custom_attribute_value_ids:
        #     if pacv.custom_product_template_attribute_value_id not in valid_values:
        #         self.product_custom_attribute_value_ids -= pacv
        #
        # # remove the no_variant attributes that don't belong to this template
        # for ptav in self.product_no_variant_attribute_value_ids:
        #     if ptav._origin not in valid_values:
        #         self.product_no_variant_attribute_value_ids -= ptav

        vals = {}
        if not self.product_uom_id or (self.product_id.uom_id.id != self.product_uom_id.id):
            vals['product_uom_id'] = self.product_id.uom_id
            vals['quantity'] = self.quantity or 1.0

        product = self.product_id.with_context(
            lang=get_lang(self.env, self.move_id.partner_id.lang).code,
            partner=self.move_id.partner_id,
            quantity=vals.get('quantity') or self.quantity,
            date=self.move_id.date,
            pricelist=self.move_id.pricelist_id.id,
            uom=self.product_uom_id.id
        )

        # vals.update(name=self.get_sale_order_line_multiline_description_sale(product))

        self._compute_tax_id()

        if self.move_id.pricelist_id and self.move_id.partner_id:
            vals['price_unit'] = self.env['account.tax']._fix_tax_included_price_company(
                self._get_display_price(product), product.taxes_id, self.tax_ids, self.company_id)
        self.update(vals)

        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s", product.name)
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
        return result

    def _compute_tax_id(self):
        for line in self:
            line = line.with_company(line.company_id)
            fpos = line.move_id.fiscal_position_id or line.move_id.fiscal_position_id.get_fiscal_position(
                line.move_id.partner_id.id)
            # If company_id is set, always filter taxes by the company
            taxes = line.product_id.taxes_id.filtered(lambda t: t.company_id == line.env.company)
            line.tax_ids = fpos.map_tax(taxes, line.product_id, line.move_id.partner_shipping_id)
