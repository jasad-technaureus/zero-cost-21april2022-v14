# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.


from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    date_order_sale_last = fields.Datetime(
        string="Order date", related="order_id.date_order", store=True, index=True
    )


#
# class PurchaseOrderLine(models.Model):
#     _inherit = 'purchase.order.line'
#
#     date_order_po_last = fields.Datetime(
#         string="Order date", related="order_id.date_order", store=True, index=True
#     )
#

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    date_order_inv_last = fields.Date(
        string="Invoice date", related="move_id.invoice_date", store=True, index=True
    )
    type = fields.Selection(related='move_id.move_type', store=True, index=True)
