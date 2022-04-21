# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields  # -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

from odoo import models, fields


class SaleBookMapping(models.Model):
    _name = 'sale.book.mapping'
    _description = "Sale Book Configuration"

    book_column = fields.Selection([('ë', 'ë'),
                                    ('f', 'f'),
                                    ('g', 'g'),
                                    ('gj', 'gj'),
                                    ('h', 'h'),
                                    ('i', 'i'),
                                    ('j', 'j'),
                                    ('k', 'k'),
                                    ('l', 'l'),
                                    ('ll', 'll'),
                                    ('m', 'm'),
                                    ('n', 'n'),
                                    ('nj', 'nj'),
                                    ('o', 'o'),
                                    ('p', 'p'),
                                    ('q', 'q'),
                                    ('r', 'r'),
                                    ('rr', 'rr'),
                                    ('s', 's'),
                                    ('sh', 'sh'),
                                    ('t', 't'),
                                    ('th', 'th'),
                                    ('u', 'u'),
                                    ('v', 'v'),
                                    ('x', 'x'),
                                    ('xh', 'xh'),
                                    ('y', 'y'),
                                    ('z', 'z'),
                                    ], string='Book Column')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')
    tax_id = fields.Many2one('account.tax', string='Taxes')
    value = fields.Selection([('exclude', 'Tax Excluded'),
                              ('tax', 'Tax')], string='Value', default='exclude')
