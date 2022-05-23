# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

{
    'name': 'Cost Adjustments',
    'version': '14.0.4.7',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Cost Adjustments',
    'description': """
       Cost Adjustments
    """,
    'website': 'https://zero.com.al',
    'author': 'Zero | Odoo Partner',
    'depends': ['auto_delivery_receipt_payment', 'stock_landed_costs'],
    'data': [
        'security/ir.model.access.csv',
        'data/automatic_cost_adjustment.xml',
        'views/stock_valuation_layer_views.xml',
        'views/stock_picking.xml',
        'views/cost_adjustment_views.xml',
        'views/res_config_settings.xml',
        'views/account_move.xml',
        'views/products_view.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
