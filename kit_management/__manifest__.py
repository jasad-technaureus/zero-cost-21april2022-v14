# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Product Kit Management',
    'version': '14.0.1.0',
    'author': 'Zero | Odoo Partner',
    'website': 'zero.com.al',
    'category': 'Inventory',
    'summary': 'Manage product kits from Sales Orders and Customer Invoices',
    'sequence': 1,
    'depends': ['account', 'sale_management', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/stock_move.xml',

    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
