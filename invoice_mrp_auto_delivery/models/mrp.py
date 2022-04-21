# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.


from odoo import fields, models, api
from odoo.http import request


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    # def button_mark_done(self):
    #     res = super(MrpProduction, self).button_mark_done()
    #     moves = self.env['stock.move'].search([('production_id', '=', self.id)])
    #     if moves:
    #         for move in moves:
    #             move.update({'real_date': self.date_finished})
    #     if self.move_raw_ids:
    #         for move in self.move_raw_ids:
    #             move.update({'real_date': self.date_finished})
    #     return res
