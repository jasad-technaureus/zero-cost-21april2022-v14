# -*- coding: utf-8 -*-
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2020. All rights reserved.

{
    'name': 'Sale and Purchase Book',
    'version': '14.0.3.2',
    'category': 'Accounting/Reports',
    'sequence': 1,
    'summary': 'Sale and Purchase Book Reports',
    'description': """
        Sale and Purchase Book Reports.
    """,
    'website': 'http://www.technaureus.com/',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/purchase_book_views.xml',
        'wizard/sales_book_views.xml',
        'views/purchase_book_config_view.xml',
        'views/sale_purchase_book_config.xml',
        'views/account_move_views.xml',
        # 'views/account_move_reversal_view.xml',

    ],
    'images': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
