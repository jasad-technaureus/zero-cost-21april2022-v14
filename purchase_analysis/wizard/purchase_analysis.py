# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import fields, models, _
from datetime import date, timedelta


class PurchaseAnalysis(models.TransientModel):
    _name = 'purchase.analysis'
    _description = 'Purchase Analysis'

    from_date = fields.Date('From')
    to_date = fields.Date('To')

    def action_open_window(self):
        self.ensure_one()
        context = dict(self.env.context, create=False, edit=True)

        def ref(module, xml_id):
            proxy = self.env['ir.model.data']
            return proxy.get_object_reference(module, xml_id)

        model, tree_view_id = ref('purchase_analysis', 'product_purchase_analysis_tree_view')
        if self.from_date and self.to_date:
            context = self._context.copy()
            context.update(dict(self.env.context, date_from=self.from_date, to_date=self.to_date))
        elif self.from_date:
            # context.update(date_from=self.from_date)
            context = self._context.copy()
            context.update(dict(self.env.context, date_from=self.from_date))
        elif self.to_date:
            context.update(date_to=self.to_date)
            context = self._context.copy()
            context.update(dict(self.env.context, to_date=self.to_date))
        views = [(tree_view_id, 'tree'), ]
        return {
            'name': _('Purchase Analysis'),
            'context': context,
            "view_mode": 'tree,form,graph',
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'views': views,
            'view_id': False,
        }
