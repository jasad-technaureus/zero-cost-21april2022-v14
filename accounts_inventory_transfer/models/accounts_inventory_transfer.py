# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    inventory_transfer_account_id = fields.Many2one('account.account', string='Account')
    is_operation_type = fields.Boolean(related='picking_id.is_operation_type')

    def create(self, vals):
        res = super(StockMove, self).create(vals)
        if not res.inventory_transfer_account_id and res.picking_id.inventory_transfer_account_id:
            res.inventory_transfer_account_id = res.picking_id.inventory_transfer_account_id
        return res

    def write(self, vals_list):
        res = super(StockMove, self).write(vals_list)
        if not self.inventory_transfer_account_id and self.picking_id.inventory_transfer_account_id:
            self.inventory_transfer_account_id = self.picking_id.inventory_transfer_account_id
        return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                  cost):
        svl_data = self.env['stock.valuation.layer'].browse(svl_id)
        acc = svl_data.inventory_transfer_account_id
        if acc:
            if svl_data.value < 0:
                debit_account_id = acc.id
            if svl_data.value > 0:
                credit_account_id = acc.id
        else:
            super(StockMove, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id, qty,
                                                             description, svl_id,
                                                             cost)
        return super(StockMove, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id, qty,
                                                                description, svl_id,
                                                                cost)


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    inventory_transfer_account_id = fields.Many2one('account.account', string='Account')

    def create(self, vals):
        res = super(StockValuationLayer, self).create(vals)
        for data in res:
            if data.stock_move_id.inventory_transfer_account_id:
                data.inventory_transfer_account_id = data.stock_move_id.inventory_transfer_account_id
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    inventory_transfer_account_id = fields.Many2one('account.account', string='Account')
    is_operation_type = fields.Boolean(default=False)

    @api.onchange('picking_type_id')
    def onchange_operation_type(self):
        if self.picking_type_id.code == 'incoming' or self.picking_type_id.code == 'outgoing':
            self.is_operation_type = True
        else:
            self.is_operation_type = False
