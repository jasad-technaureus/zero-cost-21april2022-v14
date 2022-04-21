# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Sales and Purchases Reports',
    'sequence': 1,
    'version': '14.0.1.3',
    'author': 'Zero | Odoo Partner',
    'website': 'zero.com.al',
    'category': 'Accounting',
    'summary': 'Get a detailed view of sales and purchases',
    'description': """
               Get a detailed view of sales and purchases.
    """,
    'depends': ['account', 'sale_management','zero_currency_rate'],
    'license': 'Other proprietary',
    'data': [
        'views/account_move_view.xml',
        'views/account_report_menu_view.xml',
        'views/account_move_line_template.xml'
    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
