# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.
import datetime
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet
from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo import models, fields, api, _
from odoo.tools import float_is_zero, float_repr


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def cost_adjust(self):
        view = self.env.ref('cost_adjustments.adjust_cost_wizard')
        return {
            'name': _('Cost Adjustment?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cost.adjust.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

        }


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def cost_adjust(self):
        view = self.env.ref('cost_adjustments.adjust_cost_wizard')
        return {
            'name': _('Cost Adjustment?'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cost.adjust.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',

        }
