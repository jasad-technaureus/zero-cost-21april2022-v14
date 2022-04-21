# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt.Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import api, models, fields, _
from odoo import exceptions


def isodd(x):
    return bool(x % 2)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    ean_sequence_id = fields.Many2one('ir.sequence', string='Ean sequence')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ean_sequence_id = fields.Many2one('ir.sequence', string='Ean sequence')

    @api.model
    def _get_ean_next_code(self, product):
        sequence_obj = self.env['ir.sequence']
        if product.ean_sequence_id:
            ean = sequence_obj.browse(product.ean_sequence_id.id).next_by_id()
        elif product.categ_id.ean_sequence_id:
            ean = sequence_obj.browse(product.categ_id.ean_sequence_id.id).next_by_id()
        elif product.company_id and product.company_id.ean_sequence_id:
            ean = sequence_obj.browse(product.company_id.ean_sequence_id.id).next_by_id()
        elif self.env.context.get('sequence_id', False):
            ean = sequence_obj.browse(self.env.context.get('sequence_id')).next_by_id()
        else:
            return None
        ean = (len(ean[0:6]) == 6 and ean[0:6] or
               ean[0:6].ljust(6, '0')) + ean[6:].rjust(6, '0')
        if len(ean) > 12:
            raise exceptions.Warning(
                _("Configuration Error!"
                  "The next sequence is longer than 12 characters. "
                  "It is not valid for an EAN13 needing 12 characters, "
                  "the 13 being used as a control digit"
                  "You will have to redefine the sequence or create a new one")
            )

        return ean

    def _get_ean_control_digit(self, code):
        sum = 0
        for i in range(12):
            if isodd(i):
                sum += 3 * int(code[i])
            else:
                sum += int(code[i])
        key = (10 - sum % 10) % 10
        return '%d' % key

    @api.model
    def _generate_ean13_value(self, product):

        ean = self._get_ean_next_code(product)
        if not ean:
            return None
        key = self._get_ean_control_digit(ean)
        ean13 = ean + key
        return ean13

    def generate_ean13(self, product):

        if not product.barcode or (self._context.get('overwrite') and self._context['overwrite'] == True):

            ean13 = self._generate_ean13_value(self)

            if ean13:
                return ean13
                # self.write({'barcode': ean13})

    def generate_ean13_new(self):
        ean13 = self.generate_ean13(self.browse(self.id))
        self.barcode = ean13
