# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, get_lang


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.auto_inventory and (self.operation_type_id or self.warehouse_id):
            picking = self.env['stock.picking'].search(
                [('origin', '=', self.name), ('company_id', '=', self.company_id.id)])
            print('picking-2', picking)
            for line in self.invoice_line_ids:
                price_unit = line.price_subtotal / line.quantity
                if self.currency_id != self.company_id.currency_id:
                    price_unit = (line.price_subtotal / line.quantity) * self.main_curr_rate
                if line.product_id.bom_ids and line.product_id.bom_ids.filtered(
                        lambda x: x.type == 'phantom') and self.move_type == 'out_invoice':
                    kit_product = picking.move_lines.filtered(lambda x: x.product_id == line.product_id)
                    kit_product.state = 'draft'
                    kit_product.unlink()
                    boms = line.product_id.bom_ids.filtered(lambda x: x.type == 'phantom')
                    if boms:
                        for component in boms[0].bom_line_ids:
                            if component.product_id.type != 'service':
                                new_move = self.env['stock.move'].with_context(auto_receipt=True).create(
                                    {'product_id': component.product_id.id, 'price_unit': price_unit,
                                     'name': component.product_id.name,
                                     'product_uom': component.product_uom_id.id,
                                     'product_uom_qty': component.product_qty * line.quantity,
                                     'forecast_availability': component.product_qty * line.quantity,
                                     'quantity_done': component.product_qty * line.quantity,
                                     'picking_id': picking.id,
                                     'location_id': picking.location_id.id,
                                     'location_dest_id': picking.location_dest_id.id,
                                     'real_date': self.date,
                                     })
                    context = self.env.context.copy()
                    context.update({'picking_ids_not_to_backorder': picking.id, 'auto_receipt_kit': True})
                    self.env.context = context
                    if picking.move_ids_without_package:
                        picking.with_context(auto_receipt=True, account_move=self).button_validate()
                    else:
                        picking.unlink()
                else:
                    return res
        else:
            return res
