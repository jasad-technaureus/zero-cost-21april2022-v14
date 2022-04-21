# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2021. All rights reserved.

{
    'name': 'Cumulated Balance in Currency on Journal Items',
    'version': '14.0.0.3',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Cumulated Balance in Currency on Journal Items, Debit in Currency and Credit in Currency',
    'description': """
       Cumulated Balance in Currency on Journal Items, Debit in Currency and Credit in Currency.
    """,
    'website': 'https://zero.com.al',
    'author': 'Zero | Odoo Partner',
    'depends': ['account_accountant'],
    'data': [
        'views/stock_move_line_inherit.xml'
    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
