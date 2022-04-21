# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models
import datetime


class PosSession(models.Model):
    _inherit = 'pos.session'

    def action_pos_session_closing_control(self):
        if self.config_id.customer_invoice:
            invoice_line_ids = []
            mapped_lines = []
            lines_grouped_by_dest_location = {}
            if self.update_stock_at_closing:
                self.ensure_one()
                lines_grouped_by_dest_location = {}
                picking_type = self.config_id.picking_type_id

                if not picking_type or not picking_type.default_location_dest_id:
                    session_destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
                else:
                    session_destination_id = picking_type.default_location_dest_id.id

                for order in self.order_ids:
                    if order.company_id.anglo_saxon_accounting and order.to_invoice:
                        continue

                    # order._create_order_picking()
                    picking_type = order.config_id.picking_type_id
                    if order.partner_id.property_stock_customer:
                        destination_id = order.partner_id.property_stock_customer.id
                    elif not picking_type or not picking_type.default_location_dest_id:
                        destination_id = self.env['stock.warehouse']._get_partner_locations()[0].id
                    else:
                        destination_id = picking_type.default_location_dest_id.id

                    pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(destination_id,
                                                                                              order.lines, picking_type,
                                                                                              order.partner_id)
                    pickings.write({'pos_session_id': self.id, 'pos_order_id': order.id, 'origin': order.name})

                #     if order.company_id.anglo_saxon_accounting and order.to_invoice:
                #         continue
                #     destination_id = order.partner_id.property_stock_customer.id or session_destination_id
                #     if destination_id in lines_grouped_by_dest_location:
                #         lines_grouped_by_dest_location[destination_id] |= order.lines
                #     else:
                #         lines_grouped_by_dest_location[destination_id] = order.lines
                #
                # for location_dest_id, lines in lines_grouped_by_dest_location.items():
                #     pickings = self.env['stock.picking']._create_picking_from_pos_order_lines(location_dest_id, lines,
                #                                                                               picking_type)
                #     pickings.write({'pos_session_id': self.id, 'origin': self.name})
                #     context = self._context.copy()
                #     context.update({'pospicking_new': pickings})
                #     self.env.context = context

            if self.order_ids:

                orders = self.order_ids
                for order in self.order_ids:

                    if order.account_move:
                        orders = orders - order
                if orders:
                    for order in orders:
                        order.to_invoice = True
                        order.state = 'invoiced'
                        if not order.partner_id:
                            order.partner_id = self.config_id.inv_partner_id.id
                        if order.lines:
                            for line in order.lines:
                                sim_line = orders.lines.filtered(lambda x: (x.product_id == line.product_id) and (
                                        x.price_unit == line.price_unit) and (x.discount == line.discount) and (
                                                                                   x.product_uom_id.id == line.product_uom_id.id))
                                if sim_line:
                                    tax = []
                                    qty = 0
                                    vals = {}
                                    for each in sim_line:
                                        if each.id not in mapped_lines:
                                            mapped_lines.append(each.id)
                                            qty += each.qty
                                            if each.tax_ids:
                                                for new_tax in each.tax_ids:
                                                    if new_tax.id not in tax:
                                                        tax.append(new_tax.id)
                                            vals = {
                                                'product_id': each.product_id.id,
                                                'discount': each.discount,
                                                'price_unit': each.price_unit,
                                                'name': each.product_id.display_name,
                                                'product_uom_id': each.product_uom_id.id,
                                                'tax_ids': [(6, 0, tax)],
                                                'quantity': qty
                                            }
                                    if vals:
                                        invoice_line_ids.append((0, None, vals))
                    inv_vals = {
                        'payment_reference': self.name,
                        'invoice_origin': self.name,
                        'journal_id': self.config_id.invoice_journal_id.id,
                        'move_type': 'out_invoice',
                        'ref': self.name,
                        'partner_id': self.config_id.inv_partner_id.id,
                        'narration': '',
                        # considering partner's sale pricelist's currency
                        'currency_id': self.currency_id.id,
                        'invoice_user_id': self.user_id.id,
                        'invoice_date': datetime.datetime.now().date(),
                        'invoice_line_ids': invoice_line_ids,
                        'invoice_cash_rounding_id': self.config_id.rounding_method.id if self.config_id.cash_rounding else False
                    }
                    move = self.env['account.move'].create(inv_vals)
                    # move = self.env['account.move'].search([()])
                    for ord in orders:
                        ord.account_move = move.id
                    move.sudo().with_company(self.company_id)._post()

                # move._post()
                # move.payment_state = 'paid'
                # for ord in orders:
                #     ord.account_move = move.id
        context = self.env.context.copy()
        context.update(
            {'pos_ref_name': self.name, 'config_partner': self.config_id.inv_partner_id.id, 'from_pos': True})
        self.env.context = context
        return super(PosSession, self).action_pos_session_closing_control()
