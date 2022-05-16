# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'POS Real Date on Transfers',
    'version': '14.0.0.2',
    'author': 'Zero | Odoo Partner',
    'website': 'zero.com.al',
    'category': 'Accounting',
    'summary': 'POS Real Date on Transfers',
    'sequence': 1,
    'depends': ['auto_delivery_receipt_payment', 'point_of_sale', 'cost_adjustments'],
    'data': [
        'views/stock_valuation_layer.xml'
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
