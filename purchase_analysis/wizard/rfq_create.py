# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import fields, models, _
from odoo.exceptions import UserError


class PurchaseCreationWizard(models.TransientModel):
    _name = 'purchase.create.wizard'
    _description = 'Purchase Creation Wizard'

    vendor_id = fields.Many2one('res.partner', string='Vendor')

    def action_create_rfq(self):
        if not self.vendor_id:
            raise UserError(_("Please Choose Vendor Before Proceeding!!"))
        active_ids = self._context.get('active_ids')
        po = self.env['purchase.order'].create({'partner_id': self.vendor_id.id})
        for id in active_ids:
            product = self.env['product.product'].browse(id)
            if product.to_order == 0:
                raise UserError(_("TO Order quantity can't be O !!"))
            self.env['purchase.order.line'].create(
                {'order_id': po.id, 'product_id': product.id, 'product_qty': product.to_order})
            # product.to_order = 0
