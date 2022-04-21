# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import api, models, fields, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    def action_view_product_barcode_generate(self):
        action = self.env["ir.actions.actions"]._for_xml_id("action_view_product_barcode_wizard")

        # action.update({
        #     'name': _('View Planning'),
        #     'domain': [('employee_id', 'in', self.ids)],
        #     'context': {
        #         'search_default_group_by_employee': True,
        #         'filter_employee_ids': self.ids,
        #         'hide_open_shift': True,
        #     }
        # })
        return action


class ProductBarcodeAll(models.TransientModel):
    _name = 'product.barcode.all'
    _description = 'Product Barcode All'

    overwrite = fields.Boolean('Overwrite', default=False)

    def generate_barcode_all(self):

        context = dict(self._context or {})
        context.update({'overwrite': self.overwrite})
        if self._context['active_model'] == 'product.template':
            product_obj = self.env['product.template']

            if context and context.get('active_ids', False):
                for product in context['active_ids']:
                    product_record = product_obj.search([('id', '=', product)])

                    ean13 = product_record.with_context(context).generate_ean13(product_record)
                    if ean13:
                        product_record.barcode = ean13
        elif self._context['active_model'] == 'product.product':
            product_obj = self.env['product.product']
            if context and context.get('active_ids', False):
                for product in context['active_ids']:
                    product_record = product_obj.search([('id', '=', product)])
                    ean13 = product_record.product_tmpl_id.with_context(context).generate_ean13(product_record)
                    if ean13:
                        product_record.barcode = ean13

        return True

    def action_view_product_barcode_generate(self):

        action = self.env["ir.actions.act_window"]._for_xml_id(
            "tis_product_barcode_generator.action_view_product_barcode_wizard")

        action.update({
            'context': {
                'active_ids': self._context.get('active_ids'),
                'active_model': self._context.get('active_model')
            }
        })
        # action.update({
        #     'name': _('View Planning'),
        #     'domain': [('employee_id', 'in', self.ids)],
        #     'context': {
        #         'search_default_group_by_employee': True,
        #         'filter_employee_ids': self.ids,
        #         'hide_open_shift': True,
        #     }
        # })
        return action
