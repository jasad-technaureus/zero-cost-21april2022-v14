# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    auto_inventory = fields.Boolean(string="Auto Receipt/Auto Receipt")
    operation_type_id = fields.Many2one('stock.picking.type', string="Operation Type")
    auto_payment = fields.Boolean(string="Auto Payment")
    payment_journal_id = fields.Many2one('account.journal', string='Default Journal')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
