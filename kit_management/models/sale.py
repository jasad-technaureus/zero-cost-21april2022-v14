# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.
from odoo import models, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for order_line in self:
            if order_line.product_id.is_kit:
                kit_product = order_line.move_ids.mapped('kit_line_id.product_id')
                dropship = False
                if not kit_product and any(m._is_dropshipped() for m in order_line.move_ids):
                    # boms = boms._bom_find(product=order_line.product_id, company_id=order_line.company_id.id,
                    #                       bom_type='phantom')
                    dropship = True
                # We fetch the BoMs of type kits linked to the order_line,
                # the we keep only the one related to the finished produst.
                # This bom shoud be the only one since bom_line_id was written on the moves
                # relevant_bom = boms.filtered(lambda b: b.type == 'phantom' and
                #                                        (b.product_id == order_line.product_id or
                #                                         (
                #                                                 b.product_tmpl_id == order_line.product_id.product_tmpl_id and not b.product_id)))
                if kit_product:
                    # In case of dropship, we use a 'all or nothing' policy since 'bom_line_id' was
                    # not written on a move coming from a PO.
                    # FIXME: if the components of a kit have different suppliers, multiple PO
                    # are generated. If one PO is confirmed and all the others are in draft, receiving
                    # the products for this PO will set the qty_delivered. We might need to check the
                    # state of all PO as well... but sale_mrp doesn't depend on purchase.
                    if dropship:
                        moves = order_line.move_ids.filtered(lambda m: m.state != 'cancel')
                        if moves and all(m.state == 'done' for m in moves):
                            order_line.qty_delivered = order_line.product_uom_qty
                        else:
                            order_line.qty_delivered = 0.0
                        continue
                    moves = order_line.move_ids.filtered(lambda m: m.state == 'done' and not m.scrapped)
                    filters = {
                        'incoming_moves': lambda m: m.location_dest_id.usage == 'customer' and (
                                not m.origin_returned_move_id or (m.origin_returned_move_id and m.to_refund)),
                        'outgoing_moves': lambda m: m.location_dest_id.usage != 'customer' and m.to_refund
                    }
                    order_qty = order_line.product_uom._compute_quantity(order_line.product_uom_qty,
                                                                         kit_product.uom_id)
                    order_line.qty_delivered = moves._compute_product_kit_quantities(order_line.product_id, order_qty,
                                                                                    filters)

                # If no relevant BOM is found, fall back on the all-or-nothing policy. This happens
                # when the product sold is made only of kits. In this case, the BOM of the stock moves
                # do not correspond to the product sold => no relevant BOM.
                elif kit_product:
                    if all(m.state == 'done' for m in order_line.move_ids):
                        order_line.qty_delivered = order_line.product_uom_qty
                    else:
                        order_line.qty_delivered = 0.0
