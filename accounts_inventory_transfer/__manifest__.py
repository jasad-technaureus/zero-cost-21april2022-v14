# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'Inventory Transfers with specific accounts',
    'version': '14.0.0.4',
    'category': 'Inventory',
    'sequence': 1,
    'summary': 'Inventory Transfers with specific accounts',
    'description': """
       Inventory Transfers with specific accounts.
    """,
    'website': 'https://zero.com.al',
    'author': 'Zero | Odoo Partner',
    'depends': ['stock_account'],
    'data': [
        'views/stock_picking_form_inherit.xml',
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
